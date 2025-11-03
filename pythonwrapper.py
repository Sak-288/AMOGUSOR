import ctypes
import os
from PIL import Image
import io

# Load the shared library
lib = ctypes.CDLL('./libamogus.so')

# Define function signature
lib.blur_image.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
lib.blur_image.restype = ctypes.POINTER(ctypes.c_uint8)

def blur_image(image_path, chunk_size=64):
    """
    Apply amogus blur to an image and return PIL Image object
    """
    data_size = ctypes.c_int()
    
    # Call C++ function
    result_ptr = lib.blur_image(image_path.encode('utf-8'), chunk_size, ctypes.byref(data_size))
    
    if not result_ptr or data_size.value == 0:
        return None
    
    # Copy data to Python bytes
    jpeg_data = bytes(result_ptr[:data_size.value])
    
    # Convert to PIL Image
    return Image.open(io.BytesIO(jpeg_data))