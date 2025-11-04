import numpy as np
import cv2

def region_mean_lab(image_bgr, mask_uint8, min_sat=0):
    if mask_uint8.ndim == 3:
        mask_uint8 = mask_uint8[...,0]
    mask = (mask_uint8 > 0).astype(np.uint8)

    if mask.sum() == 0:
        return (0.0, 0.0, 0.0)
    if min_sat > 0:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        sat = hsv[...,1]
        mask = cv2.bitwise_and(mask, (sat >= min_sat).astype(np.uint8))

    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    mean = cv2.mean(lab, mask=mask)[:3]
    return mean

def deltaE(lab1, lab2):
    a = np.array(lab1, dtype=np.float32)
    b = np.array(lab2, dtype=np.float32)
    return float(np.linalg.norm(a - b))
