from PIL import Image, ImageDraw
import time
import numpy as np
import os
from pre_gen_amoguses import create_blank, iterate

# Pregenerating everything : 
if not os.path.exists("pre_gen_amogus"):
    iterate()


def det_best(color, resolution):
    b, g, r = color
    r = int(r/16)
    g = int(g/16)
    b = int(b/16)
    r = r * 16
    g = g * 16
    b = b * 16

    filepath = os.path.join("pre_gen_amogus", f"{r}, {g}, {b}, {resolution}.png")
    best = Image.open(filepath)


    return best


def patch(base_image, res, spawn_x, spawn_y):
    # Variable settings | Dimensions
    width, height = base_image.size
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
                color = base_image.getpixel((x, y))
                red_total += color[0]
                green_total += color[1]
                blue_total += color[2]

    # Computing the RGB averages
    R_avg = int(red_total / area)
    G_avg = int(green_total / area)
    B_avg = int(blue_total / area)
    color_avg = (R_avg, G_avg, B_avg)

    # Getting best-fitting pre-gened amogus from db
    best = det_best(color_avg, res)

    # Pasting pre-gened onto image
    base_image.paste(best, (spawn_x, spawn_y))


# Repeating pattern all over the image
def blur_image(base_image, resolution):
    base_image = Image.open(base_image)
    img_width, img_height = base_image.size

    for x in range(0, img_width + 1, resolution):
        for y in range(0, img_height + 1, resolution):
            patch(base_image, resolution, x, y)
        
    base_image.show()

    return base_image


blur_image("paloumet.jpg", 16)