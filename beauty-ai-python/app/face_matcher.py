import cv2
import json
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
import os
from openai import OpenAI

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


class FaceMatcher:
    def __init__(self, database_url: str, openai_api_key: str | None = None):
        self.database_url = database_url
        self.face_parser = MPFaceParser()
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)

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
            return [], None

        L_cv, a_cv, b_cv = user_lab_cv
        L_std, a_std, b_std = opencv_lab_to_standard(L_cv, a_cv, b_cv)
        hue, chroma = compute_hue_chroma(a_std, b_std)
        user_tone_group = classify_tone_group(hue, a_std, b_std)

        products = get_products_from_db(self.database_url, category)

        if not products:
            print(f"No products found for category: {category}")
            return [], None

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
                "brand": row['brand'],
                "product_name": row['name'],
                "category": category,
                "shade_name": row.get('shade_name', ''),
                "price": int(row['price']) if row['price'] else 0,
                "finish": row.get('finish', ''),
                "image_url": row.get('image_url', ''),
                "color_hex": row.get('color_hex', ''),
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

    def generate_explanation(self, recommendations: List[Dict], category: str) -> List[str]:
        if not recommendations:
            return []

        try:
            category_kr = {
                "lips": "립",
                "cheeks": "치크",
                "eyes": "아이섀도우",
            }.get(category.lower(), "메이크업")

            product_block = ""
            for rank, prod in enumerate(recommendations, start=1):
                product_block += f"""
{rank}위:
- 브랜드: {prod.get('brand', '')}
- 제품명: {prod.get('product_name', '')}
- 쉐이드명: {prod.get('shade_name', '')}
- 피니쉬: {prod.get('finish', '')}
- ΔE: {prod.get('deltaE', 0):.2f}
"""

            prompt = f"""
당신은 K-뷰티 색조 전문가입니다.

아래 Top {len(recommendations)}개 {category_kr} 제품에 대해,
각각 **정확히 2문장**으로 한국어 추천 이유를 작성하세요.

제품 정보:
{product_block}

규칙:
1) 각 제품당 반드시 한국어 2문장만 작성하세요. (3문장 이상, 1문장 금지)
2) 문장에는 다음 요소를 포함하세요:
   - 색감 특징: 톤(쿨톤/웜톤/뉴트럴), 명도(밝다/중간/어둡다), 채도(선명/은은/뮤트) 중 최소 2개
   - MLBB, rosy, warm, cool, 데일리, 포인트 메이크업 등 감성 단어를 적절히 사용
   - ΔE 값이 작을수록 사용자 얼굴 색상과 더 비슷하다는 점을 자연스럽게 언급
3) 제공된 속성(브랜드, 제품명, 쉐이드명, 피니쉬, ΔE, {category_kr} 용도) 외의 정보는 절대 만들지 마세요.
   - 예: 지속력, 발림감, 향, 성분, 피부 타입, 발색력, 마케팅 문구 등은 언급 금지
4) 각 문장은 해당 제품만을 설명해야 하며, 다른 순위 제품과 혼동하지 마세요.
5) 아래 JSON 형식으로만 출력하세요. JSON 앞뒤에 다른 텍스트를 절대 추가하지 마세요.

출력 형식(JSON):

{{
  "reasons": [
    "1위 제품에 대한 한국어 2문장 설명",
    "2위 제품에 대한 한국어 2문장 설명",
    "3위 제품에 대한 한국어 2문장 설명"
  ]
}}

- reasons 배열 길이는 반드시 제품 개수({len(recommendations)})와 같아야 합니다.
- 각 요소는 하나의 문자열(string)이어야 하며, 그 안에 마침표로 구분된 2문장이 들어 있어야 합니다.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=400,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise K-beauty color analysis assistant. "
                            "You must output ONLY valid JSON that can be parsed by json.loads in Python."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            raw_text = response.choices[0].message.content.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

            try:
                data = json.loads(raw_text)
                reasons = data.get("reasons", [])
            except json.JSONDecodeError:
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end != -1:
                    json_str = raw_text[start : end + 1]
                    data = json.loads(json_str)
                    reasons = data.get("reasons", [])
                else:
                    reasons = [raw_text]

            if not isinstance(reasons, list):
                reasons = []

            while len(reasons) < len(recommendations):
                reasons.append(
                    "색상 유사도가 높고 자연스러운 얼굴 톤과 잘 어울리는 제품으로 추천되었습니다."
                )
            if len(reasons) > len(recommendations):
                reasons = reasons[: len(recommendations)]

            return reasons

        except Exception as e:
            print("LLM 에러:", e)
            return [
                "색상 유사도가 높고 자연스러운 얼굴 톤과 잘 어울리는 제품으로 추천되었습니다."
            ] * len(recommendations)