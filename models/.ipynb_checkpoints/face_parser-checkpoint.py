import cv2
import numpy as np

class SimpleFaceParser:
    def __init__(self):
        pass

    def parse(self, image_bgr):
        h, w, _ = image_bgr.shape

        masks = {
            # eyes: 위쪽 20~38% 영역
            "eyes": image_bgr[int(h*0.20):int(h*0.38), int(w*0.25):int(w*0.75)],
            # cheeks: 가운데 42~58%
            "cheeks": image_bgr[int(h*0.42):int(h*0.58), int(w*0.25):int(w*0.75)],
            # lips: 아래쪽 60~72%
            "lips": image_bgr[int(h*0.60):int(h*0.72), int(w*0.35):int(w*0.65)]
        }
        return masks