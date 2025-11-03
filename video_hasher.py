import cv2
import os
import moviepy
from moviepy import VideoFileClip
from pregened_generator import blur_image
import numpy as np


def extract_audio(mp4_file, mp3_file, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load the video clip
    video_clip = VideoFileClip(mp4_file)

    # Extract the audio from the video clip
    audio_clip = video_clip.audio

    # Write the audio to a separate file
    audio_clip.write_audiofile(mp3_file)

    # Close the video and audio clips
    audio_clip.close()
    video_clip.close()

    os.path.join(output_folder, mp3_file)


def extract_frames_and_audio(video_path, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Read and save each frame
    frame_count = 0
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Save frame as image
        frame_filename = os.path.join(output_folder, f"frame_{frame_count:06d}.jpg")
        cv2.imwrite(frame_filename, frame)
        
        frame_count += 1

    # Audio extraction
    extract_audio(video_path, "video.mp3", output_folder=output_folder)

    return int(fps)


def combine_audio(video_name, audio_name, output_file, fps=30):
    my_clip = moviepy.VideoFileClip(video_name)
    audio_background = moviepy.AudioFileClip(audio_name)
    final_clip = my_clip.with_audio(audio_background)
    final_clip.write_videofile(output_file,fps=fps)


def create_video_from_images(output_video_path, image_folder="extracted_frames", fps=30):
    # Launching the initial function
    fps = extract_frames_and_audio("video.mp4", image_folder)

    # Read first image to get dimensions
    first_image_path = os.path.join(image_folder, os.listdir(image_folder)[0])
    first_frame = cv2.imread(first_image_path)
    height, width, layers = first_frame.shape

    # Get all image files
    temp_images = [img for img in os.listdir(image_folder) if img.endswith((".jpg", ".jpeg", ".png"))]
    temp_images.sort() # Sort alphanumerically
    # images = [blur_image(os.path.join(image_folder, img), resolution, width, height) for img in temp_images]
    
    # Define video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))    
    
    # Write each image to video
    resolution = int(input('Resolution : '))
    for image in temp_images:
        image_path = os.path.join(image_folder, image)
        video_writer.write(np.asarray(blur_image(image_path, resolution)))
    
    video_writer.release()

    # Mixing audio
    combine_audio(output_video_path, "video.mp3", "final_version.mp4", fps=fps)

    # Uhhh if it works, don't fix it, patch it up
    if os.path.exists("output_video.mp4"):
        os.remove("output_video.mp4") 


create_video_from_images("output_video.mp4", "extracted_frames")
