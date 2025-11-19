import cv2
import numpy as np
import pandas as pd
import json
from typing import List, Dict, Tuple
from groq import Groq
from skimage.color import rgb2lab, deltaE_ciede2000

from .database import get_products_from_db


class ProductMatcher:
    """
    제품 이미지 분석 및 매칭 클래스
    얼굴 분석 없이 제품 이미지의 색상만으로 유사 제품 추천
    """
    
    def __init__(self, database_url: str, groq_api_key: str):
        self.database_url = database_url
        self.groq_client = Groq(api_key=groq_api_key)
    
    def extract_lab_from_bytes(self, image_bytes: bytes) -> Tuple[float, float, float]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("이미지 디코딩 실패")
        
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        avg_r, avg_g, avg_b = np.mean(rgb.reshape(-1, 3), axis=0)
        
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
        
        df["color_distance"] = distances
        return df.sort_values("color_distance").head(top_k)
    
    def build_llama_prompt(self, user_lab: Tuple[float, float, float], 
                          top3_df: pd.DataFrame) -> str:
        L, A, B = user_lab
        
        prompt = f"""당신은 전문적인 메이크업 컬러 분석 AI입니다.

사용자가 올린 제품 이미지의 대표 LAB 색상:
- L: {L:.2f}
- a: {A:.2f}
- b: {B:.2f}

아래는 ΔE2000 기준으로 가장 유사한 Top3 제품입니다.
각 제품이 왜 비슷한지, 어떤 메이크업 룩에 적합한지를 설명해주세요.

제품 정보:
"""
        
        for rank, (_, row) in enumerate(top3_df.iterrows(), start=1):
            full_name = row.get('name', '')
            if ' - ' in full_name:
                product_name, shade_name = full_name.split(' - ', 1)
            else:
                product_name = full_name
                shade_name = full_name
            
            prompt += f"""
[{rank}위 제품]
- 브랜드: {row['brand']}
- 제품명: {product_name}
- 쉐이드: {shade_name}
- 피니쉬: {row.get('finish', '')}
- ΔE 색상 거리: {row['color_distance']:.2f}
"""
        
        prompt += """
설명 규칙:
1) 각 제품당 2~3문장.
2) 왜 사용자 색과 비슷한지 (톤/채도/명도 관점에서 설명)
3) MLBB / rosy / warm / cool / 데일리 같은 감성 표현 포함
4) 너무 길게 쓰지 말고 간결하게
5) 아래 JSON 형식으로만 출력하세요.

출력 형식(JSON):
{
  "reasons": [
    "1위 제품에 대한 추천 이유",
    "2위 제품에 대한 추천 이유",
    "3위 제품에 대한 추천 이유"
  ]
}
"""
        
        return prompt
    
    def generate_reasons_with_llama(self, prompt: str) -> List[str]:
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a professional beauty color analysis AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            raw = response.choices[0].message.content.strip()
            
            try:
                data = json.loads(raw)
                reasons = data.get("reasons", [])
            except json.JSONDecodeError:
                reasons = [raw]
            
            return reasons
            
        except Exception as e:
            return ["색상 유사도가 높아 추천된 제품입니다."] * 3
    
    def recommend(self, image_bytes: bytes, category: str, top_k: int = 3) -> Tuple[Dict, List[Dict]]:
        """
        제품 이미지 기반 추천
        
        Returns:
            user_lab: {"L": float, "a": float, "b": float}
            results: List[{brand, product_name, category, shade_name, price, finish, image_url, reason}]
        """
        # 1. 이미지에서 LAB 추출
        L, A, B = self.extract_lab_from_bytes(image_bytes)
        
        # 2. Top10 매칭
        top10 = self.get_top_matches(L, A, B, category, top_k=10)
        
        if top10.empty:
            return {"L": L, "a": A, "b": B}, []
        
        # 3. Top3 선택
        top3 = top10.head(top_k).reset_index(drop=True)
        
        # 4. LLaMA 프롬프트 + 이유 생성
        prompt = self.build_llama_prompt((L, A, B), top3)
        reasons = self.generate_reasons_with_llama(prompt)
        
        while len(reasons) < len(top3):
            reasons.append("색상 유사도가 높아 추천된 제품입니다.")
        
        # 5. 최종 결과 구성
        results = []
        for i, (_, row) in enumerate(top3.iterrows()):
            full_name = row.get('name', '')
            
            if ' - ' in full_name:
                product_name, shade_name = full_name.split(' - ', 1)
            else:
                product_name = full_name
                shade_name = full_name
            
            item = {
                "brand": row["brand"],
                "product_name": product_name.strip(),
                "category": row["category"],
                "shade_name": shade_name.strip(),
                "price": int(row["price"]) if row.get("price") else 0,
                "finish": row.get("finish", ""),
                "image_url": row.get("image_url", ""),
                "color_hex": row.get("color_hex", ""),
                "reason": reasons[i].strip()
            }
            results.append(item)
        
        user_lab = {"L": L, "a": A, "b": B}
        
        return user_lab, results