from .pregened_generator import blur_image
from PIL import Image
from PIL import Image, ImageDraw
import numpy as np
import time
import random as rd
from concurrent.futures import ThreadPoolExecutor
from .check_originality import check_fast
import threading

def hash_image(img, res):
    current_image = np.array(Image.open(img))
    
    # Process the image
    img_height, img_width = current_image.shape[:2]
    
    output_height = ((img_height + res - 1) // res) * res
    output_width = ((img_width + res - 1) // res) * res
    
    result = np.zeros((output_height, output_width, 3), dtype=np.uint8)
    
    # Prepare tasks for parallel processing
    tasks = []
    for x in range(0, img_width, res):
        for y in range(0, img_height, res):
            tasks.append((current_image, res, x, y, output_height, output_width))
    
    # Process tiles in parallel
    with ThreadPoolExecutor(max_workers=min(os.cpu_count(), 4)) as executor:
        for y_start, y_end, x_start, x_end, patch_img in executor.map(process_tile, tasks):
            result[y_start:y_end, x_start:x_end] = patch_img

    print(result)