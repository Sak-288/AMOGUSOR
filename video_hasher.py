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
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imwrite(os.path.join(output_folder, f"frame_{frame_count:06d}.jpg"), frame, 
                [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_count += 1
    
    cap.release()
    
    audio_thread = threading.Thread(target=extract_audio, 
                                  args=(video_path, "video.mp3", output_folder))
    audio_thread.start()
    
    return int(fps), total_frames, audio_thread

def process_single_frame(args):
    frame_name, image_folder, resolution, width, height = args
    image_path = os.path.join(image_folder, frame_name)

    # Validate input file exists and has content
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        print(f"Warning: Empty or missing frame {frame_name}")
        raise ValueError("Invalid frame file")
        
    # Process the frame
    result = blur_image(image_path, resolution)
    
    if type(result) is str:
        result_path = result
        processed_frame = np.load(result_path)
        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_RGBA2BGR)
    else:
        processed_frame = cv2.cvtColor(result, cv2.COLOR_RGBA2BGR)

    # Resize frame to match original video dimensions
    if processed_frame.shape[:2] != (height, width):
        processed_frame = cv2.resize(processed_frame, (width, height))
    
    frame_num = int(frame_name.split('_')[1].split('.')[0])
    return frame_num, processed_frame

def combine_audio(video_name, audio_name, output_file, fps=30):
    """Audio combination"""
    my_clip = VideoFileClip(video_name)
    audio_background = AudioFileClip(audio_name)
    final_clip = my_clip.with_audio(audio_background)
    final_clip.write_videofile(output_file, fps=fps, verbose=False, logger=None)
    my_clip.close()
    audio_background.close()

def create_video_from_images_optimized(output_video_path, image_folder="extracted_frames", fps=30):
    # Extract frames and get metadata
    fps, total_frames, audio_thread = extract_frames_fast("test.mp4", image_folder)
    
    # Get dimensions from first valid frame
    first_frame_path = "extracted_frames/frame_000000.jpg"
    first_frame = cv2.imread(first_frame_path)
    
    height, width = first_frame.shape[:2]
    print(f"Video dimensions: {width}x{height}")

    # Define video writer with proper settings
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    if not video_writer.isOpened():
        print("Error: Could not open video writer")
        return
    
    # Get and sort images
    temp_images = [img for img in os.listdir(image_folder) 
                  if img.startswith("frame_") and img.endswith(".jpg")]
    temp_images.sort()
    
    # Filter out potentially corrupted frames
    valid_images = [x for x in temp_images]
    
    print(f"Found {len(valid_images)} valid frames out of {len(temp_images)} total")
    
    resolution = int(input('Resolution : '))
    
    print(f"Processing {len(valid_images)} frames with resolution {resolution}...")
    
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
                        # Ensure frame has correct dimensions and type
                        if processed_frame.dtype != np.uint8:
                            processed_frame = processed_frame.astype(np.uint8)
                        batch_results.append((frame_num, processed_frame))
                except Exception as e:
                    print(f"Future result error: {e}")
            
            # Sort this batch by frame number and write in correct order
            batch_results.sort(key=lambda x: x[0])
            for frame_num, processed_frame in batch_results:
                try:
                    video_writer.write(processed_frame)
                    frames_processed += 1
                    if frames_processed % 50 == 0:  # Progress update every 50 frames
                        print(f'Frame {frames_processed}/{len(valid_images)} processed')
                except Exception as e:
                    print(f"Error writing frame {frame_num}: {e}")
    
    video_writer.release()
    print("Video writing completed!")
    
    # Wait for audio extraction to finish
    audio_thread.join()
    
    # Mix audio with video
    print("Combining audio with video...")
    combine_audio(output_video_path, "video.mp3", "final_version.mp4", fps=fps)
    
    print("Process completed successfully!")

# TESTING
create_video_from_images_optimized("final_video.mp4", "extracted_frames")