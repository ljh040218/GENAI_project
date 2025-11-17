import cv2
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
import os
from groq import Groq

from .face_parser import MPFaceParser
from .database import get_products_from_db


def opencv_lab_to_standard(L_cv: float, a_cv: float, b_cv: float):
    L_std = L_cv * 100.0 / 255.0
    a_std = a_cv - 128.0
    b_std = b_cv - 128.0
    return L_std, a_std, b_std


def compute_hue_chroma(a_std: float, b_std: float):
    hue = np.degrees(np.arctan2(b_std, a_std)) % 360.0
    chroma = float(np.sqrt(a_std * a_std + b_std * b_std))
    return hue, chroma


def deltaE_simple(l1, a1, b1, l2, a2, b2):
    return float(np.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2))


def classify_tone_group(hue: float, a_std: float, b_std: float):
    if 10 <= hue <= 70 and b_std > 5:
        ratio = abs(a_std) / max(abs(b_std), 1e-3)
        if 1.0 <= ratio <= 3.5:
            return "coral_warm"

    if (hue >= 330 or hue <= 20) and b_std >= -5 and a_std > 10:
        return "pink_cool"

    if 280 <= hue <= 330 and b_std < 0 and a_std > 5:
        return "mauve_purple"

    if 40 <= hue <= 80 and b_std > 10 and a_std < 35:
        return "brown_orange"

    if abs(a_std) < 12 and abs(b_std) < 12:
        return "neutral_mlbb"

    return "other"


class ColorAnalyzer:
    def __init__(self, database_url: str, groq_api_key: str):
        self.database_url = database_url
        self.groq_client = Groq(api_key=groq_api_key)
        self.face_parser = MPFaceParser()

    def extract_face_colors(self, image_bgr: np.ndarray) -> Dict:
        regions = self.face_parser.parse(image_bgr)

        lab_img = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        hsv_img = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        def extract_color(mask: np.ndarray, region_type: str = "default"):
            ys, xs = np.where(mask > 0)

            if len(ys) == 0:
                return None

            if region_type == "lips":
                lab_pixels = lab_img[ys, xs, :]
                hsv_pixels = hsv_img[ys, xs, :]

                S_values = hsv_pixels[:, 1]
                V_values = hsv_pixels[:, 2]

                sat_threshold = np.percentile(S_values, 80)
                val_threshold = np.percentile(V_values, 60)

                valid_mask = (S_values >= sat_threshold) & (V_values >= val_threshold)

                if valid_mask.sum() < 10:
                    sat_threshold = np.percentile(S_values, 70)
                    val_threshold = np.percentile(V_values, 50)
                    valid_mask = (S_values >= sat_threshold) & (V_values >= val_threshold)

                if valid_mask.sum() < 5:
                    valid_mask = np.ones(len(S_values), dtype=bool)

                filtered_pixels = lab_pixels[valid_mask]
                mean = filtered_pixels.mean(axis=0)

            elif region_type == "cheeks":
                lab_pixels = lab_img[ys, xs, :]
                hsv_pixels = hsv_img[ys, xs, :]

                S_values = hsv_pixels[:, 1]
                V_values = hsv_pixels[:, 2]

                sat_threshold = np.percentile(S_values, 80)
                val_min = np.percentile(V_values, 55)
                val_max = np.percentile(V_values, 98)

                valid_mask = (S_values >= sat_threshold) & (V_values >= val_min) & (V_values <= val_max)

                if valid_mask.sum() < 50:
                    sat_threshold = np.percentile(S_values, 65)
                    valid_mask = (S_values >= sat_threshold) & (V_values >= val_min)

                if valid_mask.sum() < 20:
                    sat_threshold = np.percentile(S_values, 55)
                    valid_mask = S_values >= sat_threshold

                if valid_mask.sum() < 10:
                    valid_mask = np.ones(len(S_values), dtype=bool)

                filtered_pixels = lab_pixels[valid_mask]
                mean = filtered_pixels.mean(axis=0)

                L_mean, a_mean, b_mean = mean[0], mean[1], mean[2]

                L_boost = 20.0
                a_boost = 15.0
                b_reduce = 12.0

                L_corrected = min(L_mean + L_boost, 255.0)
                a_corrected = min(a_mean + a_boost, 255.0)
                b_corrected = max(b_mean - b_reduce, 0.0)

                mean = np.array([L_corrected, a_corrected, b_corrected])

            else:
                region_pixels = lab_img[ys, xs, :]
                mean = region_pixels.mean(axis=0)

            return float(mean[0]), float(mean[1]), float(mean[2])

        lips_lab = extract_color(regions["lips"], region_type="lips")
        cheeks_lab = extract_color(regions["cheeks"], region_type="cheeks")
        eyes_lab = extract_color(regions["eyeshadow"])

        return {
            "lips": lips_lab,
            "cheeks": cheeks_lab,
            "eyeshadow": eyes_lab,
        }

    def recommend_products(self, user_lab_cv: Tuple[float, float, float], category: str, top_k: int = 3):
        if user_lab_cv is None:
            return None, None

        L_cv, a_cv, b_cv = user_lab_cv
        L_std, a_std, b_std = opencv_lab_to_standard(L_cv, a_cv, b_cv)
        hue, chroma = compute_hue_chroma(a_std, b_std)
        user_tone_group = classify_tone_group(hue, a_std, b_std)

        products = get_products_from_db(self.database_url, category)

        if not products:
            print(f"No products found for category: {category}")
            return None, None

        df = pd.DataFrame(products)

        df['L_std'] = df['color_lab'].apply(lambda x: float(x[0]) if x and len(x) > 0 else None)
        df['a_std'] = df['color_lab'].apply(lambda x: float(x[1]) if x and len(x) > 1 else None)
        df['b_std'] = df['color_lab'].apply(lambda x: float(x[2]) if x and len(x) > 2 else None)

        df = df.dropna(subset=['L_std', 'a_std', 'b_std'])

        if category == "cheeks":
            group_df = df.copy()
        else:
            hues = []
            tone_groups = []
            for _, row in df.iterrows():
                h, _ = compute_hue_chroma(row['a_std'], row['b_std'])
                tg = classify_tone_group(h, row['a_std'], row['b_std'])
                hues.append(h)
                tone_groups.append(tg)
            df['hue'] = hues
            df['tone_group'] = tone_groups

            group_df = df[df["tone_group"] == user_tone_group].copy()

            if len(group_df) < top_k:
                group_df = df.copy()

        dE_list = []
        for _, row in group_df.iterrows():
            dE = deltaE_simple(L_std, a_std, b_std, row["L_std"], row["a_std"], row["b_std"])
            dE_list.append(dE)

        group_df["deltaE"] = dE_list
        group_df = group_df.sort_values("deltaE").head(top_k)

        results = []
        for _, row in group_df.iterrows():
            results.append({
                "id": row.get('id', ''),
                "brand": row['brand'],
                "name": row['name'],
                "price": int(row['price']) if row['price'] else 0,
                "color_hex": row.get('color_hex', ''),
                "image_url": row.get('image_url', ''),
                "deltaE": float(row['deltaE'])
            })

        user_info = {
            "user_L_std": float(L_std),
            "user_a_std": float(a_std),
            "user_b_std": float(b_std),
            "user_hue": float(hue),
            "user_chroma": float(chroma),
            "user_tone_group": user_tone_group,
        }

        return results, user_info

    def generate_explanation(self, recommendations: List[Dict], category: str) -> str:
        try:
            category_kr = {"lips": "립", "cheeks": "치크", "eyes": "아이섀도우"}.get(category, "메이크업")

            prompt = f"""You are a professional K-beauty makeup color analysis expert.

Below are the Top 3 recommended {category_kr} products based on color analysis.
Write a brief explanation for each product in polite Korean."""

            for rank, prod in enumerate(recommendations, start=1):
                prompt += f"""
{rank}위: {prod['brand']} - {prod['name']}
ΔE: {prod['deltaE']:.2f}
"""

            prompt += """
Start directly with "1위:" and write only the explanations.
"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You write Korean beauty product explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"추천 이유 생성 중 오류 발생: {str(e)}"
