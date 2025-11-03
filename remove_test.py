import os
import shutil

if os.path.exists("final_version.mp4"):
    os.remove("final_version.mp4")
if os.path.exists("output_video.mp4"):
    os.remove("output_video.mp4")
if os.path.exists("video.mp3"):
    os.remove("video.mp3")
if os.path.exists("extracted_frames"):
    shutil.rmtree("extracted_frames")
if os.path.exists("pre_gen_amogus"):
    shutil.rmtree("pre_gen_amogus")