import numpy as np
from skimage import color

def rgb_to_lab(rgb):
    rgb = np.array(rgb, dtype=np.float32) / 255.0
    lab = color.rgb2lab([[rgb]])[0][0]
    return lab

def deltaE(lab1, lab2):
    return np.linalg.norm(np.array(lab1) - np.array(lab2))

def region_mean_lab(region_bgr):
    """BGR → RGB → 평균 → LAB"""
    region_rgb = region_bgr[..., ::-1]
    mean_rgb = np.mean(region_rgb.reshape(-1, 3), axis=0)
    return rgb_to_lab(mean_rgb)