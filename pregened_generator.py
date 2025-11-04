from PIL import Image, ImageDraw
import time
import numpy as np
import os
from pre_gen_amoguses import create_blank, iterate


if not os.path.exists("pre_gen_amogus"):
    iterate()


def det_best(color, resolution):
    r, g, b = color
    r = int(r/16) * 16
    g = int(g/16) * 16
    b = int(b/16) * 16

    filepath = os.path.join("pre_gen_amogus", f"{r}, {g}, {b}, {resolution}.png")

    return filepath


def patch(base_image, res, spawn_x, spawn_y):
    # Variable settings | Dimensions
    width, height = base_image.shape[:2]
    area = res * res
    spawn = (spawn_x, spawn_y) 
    end = (spawn_x + res, spawn_y + res)

    # Getting the colors from the image
    red_total = 0
    green_total = 0
    blue_total = 0                

    # Getting colors
    for x in range(spawn[0], end[0]):
        for y in range(spawn[1], end[1]):
            if x < width and y < height: # Mandatory vibe check
                color = list(base_image[x, y])
                red_total += int(color[0])
                green_total += int(color[1])
                blue_total += int(color[2])

    # Computing the RGB averages
    R_avg = int(red_total / area)
    G_avg = int(green_total / area)
    B_avg = int(blue_total / area)
    color_avg = (R_avg, G_avg, B_avg)

    # Getting best-fitting pre-gened amogus from db
    best_filepath = det_best(color_avg, res)
    best_img = np.asarray(Image.open(best_filepath))

    return best_img

# Repeating pattern all over the image
def blur_image(base_image, resolution):
    base_image = np.asarray(Image.open(base_image))
    img_width, img_height = base_image.shape[:2]

    horizontals = []
    for x in range(0, img_width + 1, resolution):
        verticals = []
        for y in range(0, img_height + 1, resolution):
            verticals.append(patch(base_image, resolution, x, y))
        horizontals.append(verticals)

    # Unpacking, stacking, and packing
    result = np.vstack([np.hstack(row) for row in horizontals])

    final_image = Image.fromarray(result)
    
    return final_image


blur_image('youssef.jpg', 8)