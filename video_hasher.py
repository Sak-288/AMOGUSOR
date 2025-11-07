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
    """Process a single frame and return with its index"""
    frame_name, image_folder, resolution, width, height = args
    image_path = os.path.join(image_folder, frame_name)
    
    try:
        processed_frame = blur_image(image_path, resolution)
        if processed_frame.shape[:2] != (height, width):
            processed_frame = cv2.resize(processed_frame, (width, height))
        
        # Extract frame number for ordering
        frame_num = int(frame_name.split('_')[1].split('.')[0])
        return frame_num, processed_frame
    except Exception as e:
        print(f"Error processing {frame_name}: {e}")
        # Return a high number so it gets processed last
        return 999999, None

def create_video_from_images_optimized(output_video_path, image_folder="extracted_frames", fps=30):
    # Extract frames and get metadata
    fps, total_frames, audio_thread = extract_frames_fast("test.mp4", image_folder)
    
    # Get dimensions from first frame
    first_image_path = os.path.join(image_folder, "frame_000000.jpg")
    first_frame = cv2.imread(first_image_path)
    height, width = first_frame.shape[:2]

    # Define video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Get and sort images
    temp_images = [img for img in os.listdir(image_folder) 
                  if img.startswith("frame_") and img.endswith(".jpg")]
    temp_images.sort()  # This ensures frame_000000, frame_000001, etc.
    
    resolution = int(input('Resolution : '))
    
    print(f"Processing {len(temp_images)} frames with resolution {resolution}...")
    
    # Process frames in order but with parallel execution
    frames_processed = 0
    batch_size = min(8, len(temp_images) // (os.cpu_count() or 1))
    
    # Process in sequential batches to maintain order
    for batch_start in range(0, len(temp_images), batch_size):
        batch = temp_images[batch_start:batch_start + batch_size]
        
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
                frame_num, processed_frame = future.result()
                if processed_frame is not None:
                    batch_results.append((frame_num, processed_frame))
            
            # Sort this batch by frame number and write in correct order
            batch_results.sort(key=lambda x: x[0])
            for frame_num, processed_frame in batch_results:
                video_writer.write(processed_frame)
                frames_processed += 1
                print(f'Frame {frames_processed}/{len(temp_images)} processed')
    
    video_writer.release()
    
    # Wait for audio extraction to complete
    audio_thread.join()
    
    print("Video writing completed!")
    
    # Mixing audio
    combine_audio(output_video_path, "video.mp3", "final_version.mp4", fps=fps)

def combine_audio(video_name, audio_name, output_file, fps=30):
    """Audio combination"""
    my_clip = VideoFileClip(video_name)
    audio_background = AudioFileClip(audio_name)
    final_clip = my_clip.with_audio(audio_background)
    final_clip.write_videofile(output_file, fps=fps, logger=None)
    my_clip.close()
    audio_background.close()
    final_clip.close()

# Alternative even simpler approach - process in order but with threading for I/O
def create_video_simple_parallel(output_video_path, image_folder="extracted_frames", fps=30):
    """Simpler approach that maintains perfect order"""
    # Extract frames and get metadata
    fps, total_frames, audio_thread = extract_frames_fast("video.mp4", image_folder)
    
    # Get dimensions from first frame
    first_image_path = os.path.join(image_folder, "frame_000000.jpg")
    first_frame = cv2.imread(first_image_path)
    height, width = first_frame.shape[:2]

    # Define video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Get and sort images
    temp_images = [img for img in os.listdir(image_folder) 
                  if img.startswith("frame_") and img.endswith(".jpg")]
    temp_images.sort()
    
    resolution = int(input('Resolution : '))
    
    print(f"Processing {len(temp_images)} frames in order...")
    
    # Pre-load all frames for processing (memory intensive but maintains order)
    frames_to_process = [(i, img) for i, img in enumerate(temp_images)]
    
    def process_frame_ordered(args):
        idx, frame_name = args
        image_path = os.path.join(image_folder, frame_name)
        processed_frame = blur_image(image_path, resolution)
        if processed_frame.shape[:2] != (height, width):
            processed_frame = cv2.resize(processed_frame, (width, height))
        return idx, processed_frame
    
    # Process with threading but maintain order using index
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Process all frames
        future_to_idx = {executor.submit(process_frame_ordered, args): args[0] 
                        for args in frames_to_process}
        
        # Store results by index
        results = [None] * len(temp_images)
        for future in as_completed(future_to_idx):
            idx, processed_frame = future.result()
            results[idx] = processed_frame
        
        # Write in correct order
        for i, processed_frame in enumerate(results):
            if processed_frame is not None:
                video_writer.write(processed_frame)
                print(f'Frame {i+1}/{len(temp_images)} processed')
    
    video_writer.release()
    audio_thread.join()
    combine_audio(output_video_path, "video.mp3", "final_version.mp4", fps=fps)

# Choose one approach:
create_video_from_images_optimized("final_video.mp4", "extracted_frames")
