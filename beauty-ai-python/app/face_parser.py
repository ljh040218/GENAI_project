import cv2
import mediapipe as mp
import numpy as np

_FACE_OVAL = [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]
_OUTER_LIPS = [61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146]
_INNER_LIPS = [78,191,80,81,82,13,312,311,310,415,308,324,318,402,317,14,87,178,88,95]
_LEFT_EYE_RING  = [33,246,161,160,159,158,157,173,133,155,154,153,145,144,163,7]
_RIGHT_EYE_RING = [362,398,384,385,386,387,388,466,263,249,390,373,374,380,381,382]
_LEFT_EYEBROW = [70,63,105,66,107,55,65,52,53,46]
_RIGHT_EYEBROW = [300,293,334,296,336,285,295,282,283,276]

class MPFaceParser:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            refine_landmarks=True,
            max_num_faces=1
        )

    @staticmethod
    def _poly_from_idx(landmarks, idx, w, h):
        pts = np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in idx], dtype=np.int32)
        return pts.reshape(-1,1,2)

    @staticmethod
    def _fill_mask(base_image, polys):
        h, w = base_image.shape[:2]
        m = np.zeros((h, w), dtype=np.uint8)
        for p in polys:
            cv2.fillPoly(m, [p], 255)
        return m

    def parse(self, image_bgr):
        h, w = image_bgr.shape[:2]
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)
        if not result.multi_face_landmarks:
            raise ValueError("no face detected")

        lm = result.multi_face_landmarks[0].landmark
        poly_face = self._poly_from_idx(lm, _FACE_OVAL, w, h)
        poly_lips_o = self._poly_from_idx(lm, _OUTER_LIPS, w, h)
        poly_lips_i = self._poly_from_idx(lm, _INNER_LIPS, w, h)
        poly_leye = self._poly_from_idx(lm, _LEFT_EYE_RING, w, h)
        poly_reye = self._poly_from_idx(lm, _RIGHT_EYE_RING, w, h)
        poly_lebrow = self._poly_from_idx(lm, _LEFT_EYEBROW, w, h)
        poly_rebrow = self._poly_from_idx(lm, _RIGHT_EYEBROW, w, h)

        face_mask = self._fill_mask(image_bgr, [poly_face])
        lips_outer = self._fill_mask(image_bgr, [poly_lips_o])
        lips_inner = self._fill_mask(image_bgr, [poly_lips_i])
        lips_mask = cv2.subtract(lips_outer, lips_inner)
        eye_mask = self._fill_mask(image_bgr, [poly_leye, poly_reye])
        eyebrow_mask = self._fill_mask(image_bgr, [poly_lebrow, poly_rebrow])

        ys, xs = np.where(face_mask > 0)
        if len(ys) == 0:
            raise ValueError("face mask empty")
        y_min, y_max = ys.min(), ys.max()
        y_h = y_max - y_min

        nose_tip_y = int(lm[1].y * h)
        upper_lip_top_y = int(lm[0].y * h)
        eye_bottom_y = int(max(lm[145].y, lm[374].y) * h)
        start_y = int(eye_bottom_y + 0.015 * h)       
        end_y = int(nose_tip_y + (upper_lip_top_y - nose_tip_y) * 0.5)
        mid_mask = np.zeros_like(face_mask)
        mid_mask[start_y:end_y, :] = 255
        cheeks_rough = cv2.bitwise_and(face_mask, mid_mask)
        dilation_size = max(7, int(0.015 * h))
        lips_dilated = cv2.dilate(lips_mask, np.ones((dilation_size, dilation_size), np.uint8), iterations=2)
        remove_mask = cv2.bitwise_or(eye_mask, lips_dilated)
        cheeks = cv2.bitwise_and(cheeks_rough, cv2.bitwise_not(remove_mask))
        morph_size = max(5, int(0.01 * h))
        cheeks = cv2.morphologyEx(cheeks, cv2.MORPH_OPEN, np.ones((morph_size, morph_size), np.uint8))
        cheeks = cv2.morphologyEx(cheeks, cv2.MORPH_CLOSE, np.ones((morph_size+4, morph_size+4), np.uint8))

        eyeshadow = eye_mask.copy()
        dilate_size = max(12, int(0.025 * h))
        eyeshadow = cv2.dilate(eyeshadow, np.ones((dilate_size, dilate_size), np.uint8), iterations=2)
        shift = int(0.035 * h)
        M = np.float32([[1,0,0],[0,1,-shift]])
        eyeshadow_shifted = cv2.warpAffine(eyeshadow, M, (w,h), flags=cv2.INTER_NEAREST, borderValue=0)
        eyeshadow = cv2.bitwise_or(eyeshadow, eyeshadow_shifted)
        eyeshadow = cv2.subtract(eyeshadow, eye_mask)
        eyebrow_dilated = cv2.dilate(eyebrow_mask, np.ones((5,5), np.uint8), iterations=1)
        eyeshadow = cv2.subtract(eyeshadow, eyebrow_dilated)

        return {
            "lips": lips_mask.astype(np.uint8),
            "cheeks": cheeks.astype(np.uint8),
            "eyeshadow": eyeshadow.astype(np.uint8),
        }