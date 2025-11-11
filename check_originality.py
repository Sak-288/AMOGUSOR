import numpy as np
from PIL import Image
import os

def check_fast(last_one, current_one, scale_factor=0.25):
    if os.path.exists(last_one):
        img1 = Image.open(last_one).convert('L')  # Convert to grayscale as faster ig ?
    else:
        img1 = Image.open("extracted_frames/frame_000000.jpg").convert('L')  # Convert to grayscale as faster ig ?
    img2 = Image.open(current_one).convert('L')
    
    # Downscale images
    if scale_factor < 1.0:
        new_size = (int(img1.width * scale_factor), int(img1.height * scale_factor))
        img1 = img1.resize(new_size, Image.Resampling.LANCZOS)
        img2 = img2.resize(new_size, Image.Resampling.LANCZOS)
    
    array_one = np.array(img1, dtype=np.float32)
    array_two = np.array(img2, dtype=np.float32)
    
    # Constants for SSIM calculation (thx deepseek)
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    mu1 = np.mean(array_one)
    mu2 = np.mean(array_two)
    
    sigma1 = np.std(array_one)
    sigma2 = np.std(array_two)
    sigma12 = np.cov(array_one.flatten(), array_two.flatten())[0, 1]
    
    numerator = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1 ** 2 + mu2 ** 2 + C1) * (sigma1 ** 2 + sigma2 ** 2 + C2)
    
    result = float(numerator / denominator)
    return max(0.0, min(1.0, result))  # Clamp to [0, 1] because float point error