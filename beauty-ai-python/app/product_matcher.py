import cv2
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from groq import Groq
from skimage.color import rgb2lab, deltaE_ciede2000

from .database import get_products_from_db


class ProductMatcher:
    
    def __init__(self, database_url: str, groq_api_key: str):
        self.database_url = database_url
        self.groq_client = Groq(api_key=groq_api_key)
    
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
        try:
            category_kr = {"lips": "립", "cheeks": "치크", "eyes": "아이섀도우"}.get(category, "메이크업")
            
            prompt = f"""당신은 전문적인 메이크업 컬러 분석 AI입니다.

아래는 제품 이미지 색상 분석을 통해 추천된 Top3 {category_kr} 제품입니다.
각 제품에 대해 2~3문장으로 추천 이유를 설명하세요.

제품 정보:
"""
            
            for rank, prod in enumerate(recommendations, start=1):
                prompt += f"""
[{rank}위 제품]
- 브랜드: {prod['brand']}
- 제품명: {prod['product_name']}
- 쉐이드: {prod['shade_name']}
- 피니쉬: {prod['finish']}
- ΔE 색상 거리: {prod['deltaE']:.2f}
"""
            
            prompt += """
설명 규칙:
1) 각 제품당 2~3문장
2) 왜 사용자가 업로드한 제품 색상과 비슷한지 설명
3) MLBB / rosy / warm / cool / 데일리 같은 감성 표현 포함
4) 간결하게 작성
5) 아래 JSON 형식으로만 출력

출력 형식(JSON):
{
  "reasons": [
    "1위 제품에 대한 추천 이유",
    "2위 제품에 대한 추천 이유",
    "3위 제품에 대한 추천 이유"
  ]
}
"""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a professional beauty color analysis AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            raw_text = response.choices[0].message.content.strip()
            
            import json
            try:
                data = json.loads(raw_text)
                reasons = data.get("reasons", [])
            except json.JSONDecodeError:
                reasons = [raw_text]
            
            while len(reasons) < len(recommendations):
                reasons.append("색상 유사도가 높아 추천된 제품입니다.")
            
            return reasons[:len(recommendations)]
            
        except Exception:
            return ["색상 유사도가 높아 추천된 제품입니다."] * len(recommendations)