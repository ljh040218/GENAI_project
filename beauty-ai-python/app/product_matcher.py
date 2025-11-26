import cv2
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import os
from skimage.color import rgb2lab, deltaE_ciede2000
from openai import OpenAI

from .database import get_products_from_db


class ProductMatcher:
    def __init__(self, database_url: str, openai_api_key: str | None = None):
        self.database_url = database_url
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
    
    def extract_lab_from_bytes(self, image_bytes: bytes) -> Tuple[float, float, float]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("이미지 디코딩 실패")
        
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        
        center_y, center_x = h // 2, w // 2
        crop_h, crop_w = h // 3, w // 3
        
        y1 = max(0, center_y - crop_h // 2)
        y2 = min(h, center_y + crop_h // 2)
        x1 = max(0, center_x - crop_w // 2)
        x2 = min(w, center_x + crop_w // 2)
        
        center_crop = rgb[y1:y2, x1:x2]
        
        pixels = center_crop.reshape(-1, 3)
        brightness = np.mean(pixels, axis=1)
        
        lower_threshold = np.percentile(brightness, 10)
        upper_threshold = np.percentile(brightness, 90)
        
        mask = (brightness >= lower_threshold) & (brightness <= upper_threshold)
        filtered_pixels = pixels[mask]
        
        if len(filtered_pixels) < 10:
            filtered_pixels = pixels
        
        avg_r, avg_g, avg_b = np.median(filtered_pixels, axis=0)
        
        rgb_norm = np.array([[[avg_r/255, avg_g/255, avg_b/255]]])
        lab = rgb2lab(rgb_norm)[0][0]
        
        return float(lab[0]), float(lab[1]), float(lab[2])
    
    def compute_deltaE(self, L1: float, A1: float, B1: float, 
                      L2: float, A2: float, B2: float) -> float:
        color1 = np.array([[[L1, A1, B1]]])
        color2 = np.array([[[L2, A2, B2]]])
        return float(deltaE_ciede2000(color1, color2)[0][0])
    
    def get_top_matches(self, L_user: float, A_user: float, B_user: float, 
                       category: str, top_k: int = 10) -> pd.DataFrame:
        products = get_products_from_db(self.database_url, category)
        
        if not products:
            return pd.DataFrame()
        
        df = pd.DataFrame(products)
        
        df['L_std'] = df['color_lab'].apply(lambda x: float(x[0]) if x and len(x) > 0 else None)
        df['a_std'] = df['color_lab'].apply(lambda x: float(x[1]) if x and len(x) > 1 else None)
        df['b_std'] = df['color_lab'].apply(lambda x: float(x[2]) if x and len(x) > 2 else None)
        
        df = df.dropna(subset=['L_std', 'a_std', 'b_std'])
        
        distances = []
        for _, row in df.iterrows():
            dE = self.compute_deltaE(
                L_user, A_user, B_user,
                row["L_std"], row["a_std"], row["b_std"]
            )
            distances.append(dE)
        
        df["deltaE"] = distances
        df_sorted = df.sort_values("deltaE")
        
        unique_products = []
        seen_names = set()
        
        for _, row in df_sorted.iterrows():
            product_key = f"{row['brand']}_{row['name']}"
            
            if product_key not in seen_names:
                unique_products.append(row)
                seen_names.add(product_key)
                
                if len(unique_products) >= top_k:
                    break
        
        return pd.DataFrame(unique_products)
    
    def recommend(self, image_bytes: bytes, category: str, top_k: int = 3) -> Tuple[Dict, List[Dict]]:
        L, A, B = self.extract_lab_from_bytes(image_bytes)
        
        top_matches = self.get_top_matches(L, A, B, category, top_k=top_k)
        
        if top_matches.empty:
            return {"L": L, "a": A, "b": B}, []
        
        top_results = top_matches.head(top_k).reset_index(drop=False)
        
        results = []
        for _, row in top_results.iterrows():
            item = {
                "brand": row["brand"],
                "product_name": row["name"],
                "category": row["category"],
                "shade_name": row.get("shade_name", ""),
                "price": int(row["price"]) if row.get("price") else 0,
                "finish": row.get("finish", ""),
                "image_url": row.get("image_url", ""),
                "color_hex": row.get("color_hex", ""),
                "deltaE": float(row["deltaE"])
            }
            results.append(item)
        
        user_lab = {"L": L, "a": A, "b": B}
        
        return user_lab, results
    
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
   - ΔE 값이 작을수록 사용자가 업로드한 색상과 더 비슷하다는 점을 자연스럽게 언급
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
                    "색상 유사도가 높고 원본 컬러와 자연스럽게 어우러지는 제품으로 추천되었습니다."
                )
            if len(reasons) > len(recommendations):
                reasons = reasons[: len(recommendations)]

            return reasons

        except Exception as e:
            print("LLM 에러:", e)
            return [
                "색상 유사도가 높고 원본 컬러와 자연스럽게 어우러지는 제품으로 추천되었습니다."
            ] * len(recommendations)