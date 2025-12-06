import cv2
import os
import moviepy
from moviepy import VideoFileClip, AudioFileClip
from .pregened_generator import blur_image
import numpy as np
import threading
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import tempfile
from collections import OrderedDict

# This is a blurring alternative
from .image_hasher import hash_image

def extract_audio(mp4_file, mp3_file, output_folder):
    """Extract audio in background"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video_clip = VideoFileClip(mp4_file)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(mp3_file, logger=None)
    audio_clip.close()
    video_clip.close()

def extract_frames_fast(video_path, output_folder):
    """Optimized frame extraction with better compression"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    dir = "usage/"
    # Start audio extraction immediately in background
    audio_thread = threading.Thread(target=extract_audio, 
                                  args=(video_path, dir + "video.mp3", output_folder))
    audio_thread.start()
    
    # Extract frames with lower quality to save disk I/O time
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break      
        
        cv2.imwrite(os.path.join(output_folder, f"frame_{frame_count:06d}.jpg"), frame, 
                [cv2.IMWRITE_JPEG_QUALITY, 70])  # Lower quality for faster I/O
        frame_count += 1
    
    cap.release()
    
    return int(fps), total_frames, audio_thread                   

def process_single_frame(args):
    frame_name, image_folder, resolution, width, height = args
    image_path = os.path.join(image_folder, frame_name)
    dir = "usage/"

    # Quick file validation
    if not os.path.exists(image_path):
        raise ValueError(f"Missing frame {frame_name}")
        
    # Process the frame
    result = blur_image(image_path, resolution)
    
    if isinstance(result, str):
        try:
            processed_frame = np.load(result)
        except:
            processed_frame = hash_image(image_path, resolution)
        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_RGBA2BGR)
    else:
        processed_frame = cv2.cvtColor(result, cv2.COLOR_RGBA2BGR)

    # Only resize if necessary
    if processed_frame.shape[1] != width or processed_frame.shape[0] != height:
        processed_frame = cv2.resize(processed_frame, (width, height))
    
    frame_num = int(frame_name.split('_')[1].split('.')[0])
    return frame_num, processed_frame
         
def combine_audio(video_name, audio_name, output_file, fps=30):
    """Fast audio combination"""
    my_clip = VideoFileClip(video_name)
    audio_background = AudioFileClip(audio_name)
    final_clip = my_clip.with_audio(audio_background)
    final_clip.write_videofile(output_file, fps=fps, logger=None, 
                             threads=4, preset='fast')
    my_clip.close()
    audio_background.close()

def create_video_from_images_optimized(output_video_path, input_video_path, resolution, image_folder="extracted_frames", fps=30):
    # Extract frames and get metadata
    fps, total_frames, audio_thread = extract_frames_fast(input_video_path, image_folder)
    
    # Get dimensions from first frame
    first_frame_path = os.path.join(image_folder, "frame_000000.jpg")
    first_frame = cv2.imread(first_frame_path)
    
    if first_frame is None:
        print("Error: Could not read first frame")
        return
        
    height, width = first_frame.shape[:2]
    print(f"Video dimensions: {width}x{height}")

    # Define video writer with better codec
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    if not video_writer.isOpened():
        print("Error: Could not open video writer")
        return
    
    # Get and sort images
    temp_images = [img for img in os.listdir(image_folder) 
                  if img.startswith("frame_") and img.endswith(".jpg")]
    temp_images.sort()
    
    print(f"Found {len(temp_images)} frames to process")
    
    print(f"Processing {len(temp_images)} frames with resolution {resolution}...")
    
    num_workers = min(os.cpu_count(), 4)  # Cap at 8 workers
    batch_size = max(1, len(temp_images) // (num_workers * 2))  # Smaller batches for better load balancing
    
    frames_processed = 0
    progress_interval = max(1, len(temp_images) // 20)  # Show progress ~20 times
    
    for batch_start in range(0, len(temp_images), batch_size):
        batch = temp_images[batch_start:batch_start + batch_size]
        
        # Prepare arguments for this batch
        frame_args = [(frame_name, image_folder, resolution, width, height) 
                     for frame_name in batch]
        
        # Process current batch in parallel
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Use map instead of submit for simpler execution
            results = executor.map(process_single_frame, frame_args)
            
            # Collect and sort results for this batch
            batch_results = []
            for result in results:
                if result is not None:
                    batch_results.append(result)
            
            # Sort by frame number and write in correct order
            batch_results.sort(key=lambda x: x[0])
            for frame_num, processed_frame in batch_results:
                video_writer.write(processed_frame)
                frames_processed += 1
                
                if frames_processed % progress_interval == 0:
                    print(f'Progress: {frames_processed}/{len(temp_images)} frames ({frames_processed/len(temp_images)*100:.1f}%)')
    
    video_writer.release()
    print("Video writing completed!")
    
    # Wait for audio extraction to finish
    audio_thread.join()
    
    dir = "usage/"
    # Mix audio with video
    print("Combining audio with video...")
    combine_audio(dir + "output.mp4", dir + "video.mp3", "webapp/static/webapp/final_version_with_audio.mp4", fps=fps)
    
    print("Process completed successfully!")


dir = "media/my_uploads/"
entry_list = [x for x in os.scandir(dir)]
create_video_from_images_optimized("usage/output.mp4", dir + entry_list[0].name, 16, "usage/extracted_frames")
accessPath = "webapp/static/webapp/final_version_with_audio.mp4"

