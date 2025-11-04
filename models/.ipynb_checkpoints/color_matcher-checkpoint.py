import numpy as np
from skimage import color

def rgb_to_lab(rgb):
    rgb = np.array(rgb, dtype=np.float32) / 255.0
    return color.rgb2lab([[rgb]])[0][0]

def deltaE(lab1, lab2):
    return np.linalg.norm(np.array(lab1) - np.array(lab2))