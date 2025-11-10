from PIL import Image, ImageDraw
import time
import numpy as np
import os
from pre_gen_amoguses import create_blank, iterate
import cv2
import random as rd
from concurrent.futures import ThreadPoolExecutor

# Checking if we have all the pregen'ed amoguses in the directory
if not os.path.exists("pre_gen_amogus"):
    iterate()
elif not os.listdir("pre_gen_amogus"):
    iterate()

# Cache for pre-loaded images
_image_cache = {}

def det_best(color, resolution):
    b, g, r = color
    r = int(r/16) * 16
    g = int(g/16) * 16
    b = int(b/16) * 16

    filepath = os.path.join("pre_gen_amogus", f"{r}, {g}, {b}, {resolution}.png")
    return filepath

def get_cached_image(filepath, size=None):
    """Cache images to avoid repeated disk I/O"""
    key = (filepath, size) if size else filepath
    if key not in _image_cache:
        img = np.asarray(Image.open(filepath))
        if size:
            img = cv2.resize(img, size)
        _image_cache[key] = img
    return _image_cache[key]

def patch(base_image, res, spawn_x, spawn_y):
    height, width = base_image.shape[:2]
    
    # Calculate safe boundaries
    end_x = min(spawn_x + res, width)
    end_y = min(spawn_y + res, height)
    actual_res_x = end_x - spawn_x
    actual_res_y = end_y - spawn_y
    
    # Vectorized sampling for much faster color averaging
    sample_size = min(actual_res_x * actual_res_y, 100) # Limit sample sizesample_size

    # Only 4 in each line (x, y)
    size_fourth = int((end_x - spawn_x)/ 4)

    # Vectorized color extraction
    samples = base_image[np.array([x for x in range(spawn_x, end_x + 1, size_fourth) if x < width]), np.array([y for y in range(spawn_y, end_y + 1, size_fourth) if y < height])]
    print(samples)
    
    # Fast average calculation
    color_avg = np.mean(samples, axis=0).astype(np.uint8)
    
    # Get pre-generated amogus with caching
    best_filepath = det_best(color_avg, res)
    
    if actual_res_x != res or actual_res_y != res:
        best_img = get_cached_image(best_filepath, (actual_res_x, actual_res_y))
    else:
        best_img = get_cached_image(best_filepath)
    
    return best_img

def process_tile(args):
    """Process a single tile for parallel execution"""
    base_image, resolution, x, y, output_height, output_width = args
    patch_img = patch(base_image, resolution, x, y)
    
    end_x = min(x + resolution, output_width)
    end_y = min(y + resolution, output_height)
    patch_height = end_y - y
    patch_width = end_x - x
    
    if patch_img.shape[0] != patch_height or patch_img.shape[1] != patch_width:
        patch_img = cv2.resize(patch_img, (patch_width, patch_height))
    
    return (y, end_y, x, end_x, patch_img)

def blur_image(base_image, resolution):
    base_image = np.asarray(Image.open(base_image))
    img_height, img_width = base_image.shape[:2]
    
    output_height = ((img_height + resolution - 1) // resolution) * resolution
    output_width = ((img_width + resolution - 1) // resolution) * resolution
    
    result = np.zeros((output_height, output_width, 3), dtype=np.uint8)
    
    # Prepare tasks for parallel processing
    tasks = []
    for x in range(0, img_width, resolution):
        for y in range(0, img_height, resolution):
            tasks.append((base_image, resolution, x, y, output_height, output_width))
    
    # Process tiles in parallel
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        for y_start, y_end, x_start, x_end, patch_img in executor.map(process_tile, tasks):
            result[y_start:y_end, x_start:x_end] = patch_img
    
    img = Image.fromarray(result)
    img.show()
    return result

for i in range(0, 4):
    blur_image('youssef.jpg', 8)