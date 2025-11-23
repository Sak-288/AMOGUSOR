from .pregened_generator import blur_image
from PIL import Image
from PIL import Image, ImageDraw
import numpy as np
import time
import random as rd
from concurrent.futures import ThreadPoolExecutor
from .check_originality import check_fast
import threading
import os

def det_best(color, resolution):
    b, g, r = color # BGR for image, RGB for video -- Don't have an explication, just roll with it
    r = int(r/16) * 16
    g = int(g/16) * 16
    b = int(b/16) * 16

    filepath = os.path.join("pre_gen_amogus", f"{r}, {g}, {b}, {resolution}.png")
    return filepath

def patch(base_image, res, spawn_x, spawn_y):
    height, width = base_image.shape[:2]
    
    end_x = min(spawn_x + res, width)
    end_y = min(spawn_y + res, height)
    actual_res_x = end_x - spawn_x
    actual_res_y = end_y - spawn_y
    
    # Vectorized sampling for much faster color averaging
    sample_size = min(actual_res_x * actual_res_y, 100)

    # Yeah only four is pretty much enough to get the gist
    size_fourth = int((end_x - spawn_x)/ 4)

    # Vectorized color extraction (apparently, i barely know what vectorized means, but godspeed to stackoverflow)
    try:
        samples = base_image[np.array([y for y in range(spawn_y, end_y + 1, size_fourth) if y < height]), np.array([x for x in range(spawn_x, end_x + 1, size_fourth) if x < width])]
    except IndexError:
        samples = base_image[np.array([0, 0, 0, 0, 0]), np.array([0, 0, 0, 0, 0])]

    # Fast average calculation (NUMPY MY GOAT AT IT AGAIN, YOU SHOULD BE GETTING TIRED OF WINNING !)
    color_avg = np.mean(samples, axis=0).astype(np.uint8)
    
    best_filepath = det_best(color_avg, res)
    best_img = np.asarray(Image.open(best_filepath))

    return best_img

def process_tile(args):
    base_image, resolution, x, y, output_height, output_width = args
    patch_img = patch(base_image, resolution, x, y)
    
    end_x = min(x + resolution, output_width)
    end_y = min(y + resolution, output_height)
    patch_height = end_y - y
    patch_width = end_x - x
    
    if patch_img.shape[0] != patch_height or patch_img.shape[1] != patch_width:
        patch_img = cv2.resize(patch_img, (patch_width, patch_height))
    
    return (y, end_y, x, end_x, patch_img)

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

    img = Image.fromarray(result)
    img.show()
    return result