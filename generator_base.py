from PIL import Image, ImageDraw
import time
import numpy as np

# Drawing ONE Amogus Pattern
def amogus_pattern(img, w, h, spawn_x, spawn_y, width, height):
    # Variable settings | Dimensions
    area = w * h
    spawn = (spawn_x, spawn_y) 
    end = (spawn_x + w, spawn_y + h)

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

    # Getting the colors from the image
    red_total = 0
    green_total = 0
    blue_total = 0


    for x in range(spawn[0], end[0] + 1):
        for y in range(spawn[1], end[1] + 1):
            if x < width and y < height: # Mandatory vibe check
                color = img.getpixel((x, y))
                red_total, green_total, blue_total = color


    # Computing the RGB averages
    R_avg = int(red_total / area)
    G_avg = int(green_total / area)
    B_avg = int(blue_total / area)
    color_avg = (R_avg, G_avg, B_avg)
    lighter_color_avg = (round(R_avg * 5/4), round(G_avg * 5/4), round(B_avg * 5/4))
    darker_color_avg = (round(R_avg * 3/4), round(G_avg * 3/4), round(B_avg * 3/4))

    # Actually blurring in the shape of Amogus
    for x in range(spawn[0], end[0] + 1):
        for y in range(spawn[1], end[1] + 1):
            if x < width and y < height: # Mandatory vibe check
                b, e, l = check_dead_zones(x, y)
                if b is False and e is False and l is False:
                    img.putpixel((x, y), color_avg)
                elif b is False and l is False and e is True:
                    img.putpixel((x, y), lighter_color_avg)
                elif e is False and (b is True or l is True):
                    img.putpixel((x, y), darker_color_avg)
                    

# Repeating pattern all over the image
def blur_image(frame, chunk_size):
    img = Image.open(frame)

    chunkH = chunk_size
    chunkW = chunk_size

    img_width, img_height = img.size

    for x in range(0, img_width + 1, chunk_size):
        for y in range(0, img_height + 1, chunk_size):
            amogus_pattern(img, chunkW, chunkH, x, y, img_width, img_height)

    img.show()
    

blur_image("youssef.jpg", 4)