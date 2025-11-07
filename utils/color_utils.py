import numpy as np
import cv2

def region_mean_lab(image_bgr, mask_uint8, min_sat=0, use_top_saturation=False, top_percent=0.3):
    if mask_uint8.ndim == 3:
        mask_uint8 = mask_uint8[...,0]
    mask = (mask_uint8 > 0).astype(np.uint8)

    if mask.sum() == 0:
        return (0.0, 0.0, 0.0)
    
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[...,1]
    
    if use_top_saturation:
        masked_sat = sat[mask > 0]
        if len(masked_sat) == 0:
            return (0.0, 0.0, 0.0)
        
        threshold_value = np.percentile(masked_sat, (1 - top_percent) * 100)
        mask = cv2.bitwise_and(mask, (sat >= threshold_value).astype(np.uint8))
    elif min_sat > 0:
        mask = cv2.bitwise_and(mask, (sat >= min_sat).astype(np.uint8))

    if mask.sum() == 0:
        return (0.0, 0.0, 0.0)

    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    mean = cv2.mean(lab, mask=mask)[:3]
    return mean

def region_mean_lab_spatial(image_bgr, mask_uint8, center_weight=0.7):
    if mask_uint8.ndim == 3:
        mask_uint8 = mask_uint8[...,0]
    mask = (mask_uint8 > 0).astype(np.uint8)
    
    if mask.sum() == 0:
        return (0.0, 0.0, 0.0)
    
    kernel_size = max(5, int(0.02 * image_bgr.shape[0]))
    eroded_mask = cv2.erode(mask, np.ones((kernel_size, kernel_size), np.uint8), iterations=1)
    
    if eroded_mask.sum() == 0:
        eroded_mask = mask
    
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    
    center_mean = cv2.mean(lab, mask=eroded_mask)[:3]
    full_mean = cv2.mean(lab, mask=mask)[:3]
    
    result = tuple(
        center_weight * center_mean[i] + (1 - center_weight) * full_mean[i]
        for i in range(3)
    )
    
    return result

def region_mean_lab_variance_filter(image_bgr, mask_uint8, variance_threshold=20):
    if mask_uint8.ndim == 3:
        mask_uint8 = mask_uint8[...,0]
    mask = (mask_uint8 > 0).astype(np.uint8)
    
    if mask.sum() == 0:
        return (0.0, 0.0, 0.0)
    
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    
    masked_pixels = lab[mask > 0]
    if len(masked_pixels) == 0:
        return (0.0, 0.0, 0.0)
    
    pixel_variances = np.var(masked_pixels, axis=1)
    
    high_variance_pixels = masked_pixels[pixel_variances > variance_threshold]
    
    if len(high_variance_pixels) > len(masked_pixels) * 0.1:
        mean = np.mean(high_variance_pixels, axis=0)
    else:
        mean = np.mean(masked_pixels, axis=0)
    
    return tuple(mean)

def deltaE(lab1, lab2):
    a = np.array(lab1, dtype=np.float32)
    b = np.array(lab2, dtype=np.float32)
    return float(np.linalg.norm(a - b))