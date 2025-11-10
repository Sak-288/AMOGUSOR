import cv2
import os
import moviepy
from moviepy import VideoFileClip, AudioFileClip
from pregened_generator import blur_image
import numpy as np
import threading
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
from collections import OrderedDict

# Add this at the beginning of your script
def cleanup_old_files():
    """Clean up any leftover temporary files from previous runs"""
    import glob
    patterns = ["temp_result_*.npy", "last_result.npy", "global_variables.json"]
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
            except:
                pass

# Call this before starting video processing
cleanup_old_files()

def extract_audio(mp4_file, mp3_file, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video_clip = VideoFileClip(mp4_file)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(mp3_file, logger=None)
    audio_clip.close()
    video_clip.close()

def extract_frames_fast(video_path, output_folder):
    """Optimized frame extraction"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Extract frames efficiently
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imwrite(os.path.join(output_folder, f"frame_{frame_count:06d}.jpg"), frame, 
                   [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_count += 1
    
    cap.release()
    
    # Extract audio in background thread
    audio_thread = threading.Thread(target=extract_audio, 
                                  args=(video_path, "video.mp3", output_folder))
    audio_thread.start()
    
    return int(fps), total_frames, audio_thread

def process_single_frame(args):
    """Process a single frame with robust error handling and validation"""
    frame_name, image_folder, resolution, width, height = args
    image_path = os.path.join(image_folder, frame_name)
    
    try:
        # Validate input file exists and has content
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            print(f"Warning: Empty or missing frame {frame_name}")
            raise ValueError("Invalid frame file")
        
        # Process the frame
        result_path = blur_image(image_path, resolution)
        
        # Load and validate the result
        if not os.path.exists(result_path) or os.path.getsize(result_path) == 0:
            print(f"Warning: Empty result for {frame_name}")
            raise ValueError("Invalid result file")
            
        processed_frame = np.load(result_path)
        
        # Validate the loaded array
        if processed_frame.size == 0:
            print(f"Warning: Empty array for {frame_name}")
            raise ValueError("Empty array")
        
        # Ensure correct data type
        if processed_frame.dtype != np.uint8:
            processed_frame = processed_frame.astype(np.uint8)
        
        # Handle different array shapes
        if len(processed_frame.shape) == 2:  # Grayscale
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_GRAY2BGR)
        elif processed_frame.shape[2] == 4:  # RGBA
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_RGBA2BGR)
        elif len(processed_frame.shape) != 3 or processed_frame.shape[2] != 3:
            print(f"Warning: Unexpected shape {processed_frame.shape} for {frame_name}")
            # Force reshape to expected dimensions
            processed_frame = processed_frame.reshape(height, width, 3)
        
        # Resize if dimensions don't match
        if processed_frame.shape[:2] != (height, width):
            try:
                processed_frame = cv2.resize(processed_frame, (width, height))
            except Exception as resize_error:
                print(f"Resize failed for {frame_name}: {resize_error}")
                # Create blank frame as fallback
                processed_frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Final validation
        if processed_frame.shape != (height, width, 3):
            print(f"Final shape mismatch for {frame_name}: {processed_frame.shape}")
            processed_frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Extract frame number for ordering
        frame_num = int(frame_name.split('_')[1].split('.')[0])
        return frame_num, processed_frame
        
    except Exception as e:
        print(f"Error processing {frame_name}: {e}")
        # Create a validated blank frame
        blank_frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame_num = int(frame_name.split('_')[1].split('.')[0])
        return frame_num, blank_frame

def create_video_from_images_optimized(output_video_path, image_folder="extracted_frames", fps=30):
    # Extract frames and get metadata
    fps, total_frames, audio_thread = extract_frames_fast("test.mp4", image_folder)
    
    # Get dimensions from first valid frame
    first_frame_path = None
    for i in range(100):  # Check first 100 frames
        test_path = os.path.join(image_folder, f"frame_{i:06d}.jpg")
        if os.path.exists(test_path) and os.path.getsize(test_path) > 0:
            first_frame_path = test_path
            break
    
    if not first_frame_path:
        raise ValueError("No valid frames found!")
    
    first_frame = cv2.imread(first_frame_path)
    if first_frame is None:
        raise ValueError("Could not read first frame")
    
    height, width = first_frame.shape[:2]
    print(f"Video dimensions: {width}x{height}")

    # Define video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Get and sort images
    temp_images = [img for img in os.listdir(image_folder) 
                  if img.startswith("frame_") and img.endswith(".jpg")]
    temp_images.sort()
    
    # Filter out potentially corrupted frames
    valid_images = []
    for img in temp_images:
        img_path = os.path.join(image_folder, img)
        if os.path.getsize(img_path) > 0:
            valid_images.append(img)
        else:
            print(f"Skipping empty frame: {img}")
    
    print(f"Found {len(valid_images)} valid frames out of {len(temp_images)} total")
    
    resolution = int(input('Resolution : '))
    
    print(f"Processing {len(valid_images)} frames with resolution {resolution}...")
    
    # Use smaller batch size to reduce memory pressure
    batch_size = min(4, len(valid_images) // (os.cpu_count() or 1))
    frames_processed = 0
    
    for batch_start in range(0, len(valid_images), batch_size):
        batch = valid_images[batch_start:batch_start + batch_size]
        
        # Prepare arguments for this batch
        frame_args = [(frame_name, image_folder, resolution, width, height) 
                     for frame_name in batch]
        
        # Process current batch in parallel
        with ThreadPoolExecutor(max_workers=min(os.cpu_count(), batch_size)) as executor:
            # Submit all tasks
            future_to_frame = {executor.submit(process_single_frame, args): args[0] 
                             for args in frame_args}
            
            # Collect results for this batch
            batch_results = []
            for future in as_completed(future_to_frame):
                try:
                    frame_num, processed_frame = future.result()
                    if processed_frame is not None:
                        batch_results.append((frame_num, processed_frame))
                except Exception as e:
                    print(f"Future result error: {e}")
            
            # Sort this batch by frame number and write in correct order
            batch_results.sort(key=lambda x: x[0])
            for frame_num, processed_frame in batch_results:
                video_writer.write(processed_frame)
                frames_processed += 1
                if frames_processed % 50 == 0:  # Progress update every 50 frames
                    print(f'Frame {frames_processed}/{len(valid_images)} processed')
    
    video_writer.release()
    
    # Wait for audio extraction to complete
    audio_thread.join()
    
    print("Video writing completed!")
    
    # Clean up temporary files
    cleanup_temp_files()
    
    # Mixing audio
    combine_audio(output_video_path, "video.mp3", "final_version.mp4", fps=fps)

    def cleanup_temp_files():
        """Clean up temporary numpy files"""
        import glob
        temp_files = glob.glob("temp_result_*.npy") + glob.glob("last_result.npy")
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

# TESTING
create_video_from_images_optimized("final_video.mp4", "extracted_frames")
