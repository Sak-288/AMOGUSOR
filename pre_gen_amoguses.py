from PIL import Image, ImageDraw
import cv2
import time
import numpy as np
import os

sizes = [8, 16, 24, 32, 40, 48, 56, 64]

def create_blank(width, height):
    blank = Image.new("RGB", (width, height), color=(255, 255, 255))

    return blank

# Drawing ONE Amogus Pattern
def amogus_pattern(img, w, h, spawn_x=0, spawn_y=0, color=(0, 0, 0)):
    # Variable settings | Dimensions
    area = w * h
    spawn = (spawn_x, spawn_y) 
    end = (spawn_x + w - 1, spawn_y + h - 1)
    # Color Stuff
    color_avg = color
    r_avg, g_avg, b_avg = color_avg
    lighter_color_avg = (int(r_avg * 5/4), int(g_avg * 5/4), int(b_avg * 5/4))
    darker_color_avg = (int(r_avg * 3/4), int(g_avg * 3/4), int(b_avg * 3/4))

    # Dead Zones Booleans | The shape of the Amogus
    def check_dead_zones(x, y):
        if x <= int(spawn[0] + 1/4 * w) and (y <= int(spawn[1] + 1/4 * h) or y >= int(spawn[1] + 3/4 * h)):
            isBackpack = True
        else:
            isBackpack = False

        if x >= int(spawn[0] + 1/2 * w) and x <= int(end[0]) and y >= int(spawn[1] + 1/8 * h) and y <= int(spawn[1] + 3/8 * h):
            isEyes = True
        else:
            isEyes = False     

        if x >= int(spawn[0] + 1/2 * w) and x <= int(spawn[0] + 3/4 * w) and y >= int(spawn[1] + 7/8 * h) and y <= int(end[1]):
            isLegspace = True
        else:
            isLegspace = False
        
        return isBackpack, isEyes, isLegspace


    # Actually blurring in the shape of Amogus
    for x in range(spawn[0], end[0] + 1):
        for y in range(spawn[1], end[1] + 1):
            b, e, l = check_dead_zones(x, y)
            if b is False and e is False and l is False:
                try:
                    img.putpixel((x, y), color_avg)
                except IndexError:
                    pass
            elif b is False and l is False and e is True:
                try:
                    img.putpixel((x, y), lighter_color_avg)
                except IndexError:
                    pass
            elif e is False and (b is True or l is True):
                try:
                    img.putpixel((x, y), darker_color_avg)
                except IndexError:
                    pass

    return np.asarray(img)


# Repeating pattern all over the image
def blur_image(frame, chunk_size, color):
    img = frame
    chunkH = chunk_size
    chunkW = chunk_size

    img_width, img_height = img.size

    for x in range(0, img_width + 1, chunk_size):
        for y in range(0, img_height + 1, chunk_size):
            amogus_pattern(img, chunkW, chunkH, x, y, color)

    return np.asarray(img)


def iterate():
    i = 0
    if not os.path.exists("pre_gen_amogus"):
        os.makedirs("pre_gen_amogus")
    for size in range(8, 65, 8):
        for r in range(0, 256, 16):
            for g in range(0, 256, 16):
                for b in range(0, 256, 16):
                    i += 1
                    start = time.perf_counter()
                    img = blur_image(create_blank(size, size), size, (r, g, b))
                    img_path = os.path.join("pre_gen_amogus", f"{r}, {g}, {b}, {size}.png")
                    cv2.imwrite(img_path, np.asarray(img))
                    end = time.perf_counter()
                    elapsed = end - start
                    print(f'Amogus number {i} made after {elapsed}')