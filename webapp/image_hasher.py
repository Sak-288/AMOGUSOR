from .pregened_generator import blur_image

def hash_image(img, res):
    img = blur_image(img, res)
    return img