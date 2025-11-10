import numpy as np
import os
from skimage.metrics import structural_similarity as ssim
from PIL import Image

dir_path = "extracted_frames/"

if not os.path.exists(dir_path):
    os.makedirs(dir_path)

images = [img for img in os.listdir(dir_path)]
images.sort()

def check(last_one, current_one):
    img_one = last_one
    img_two = current_one
    
    array_one = np.array(Image.open(img_one))
    array_two = np.array(Image.open(img_two))
    
    height, width = array_one.shape[:2]
    
    max_win_size = min(height, width)
    win_size = min(7, max_win_size) 

    if win_size % 2 == 0:
        win_size = max(3, win_size - 1)
    
    if len(array_one.shape) == 3:
        ssim_score = ssim(array_one, array_two, win_size=win_size, channel_axis=2)
    
    return float(ssim_score)