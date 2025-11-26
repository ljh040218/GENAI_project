import os
import json
import psycopg2
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
import numpy as np


class VectorDB:
    def __init__(self, database_url: str, openai_api_key: str | None = None):
        self.database_url = database_url
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
    
    def get_connection(self):
        return psycopg2.connect(self.database_url)
    
    def create_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def save_feedback(
        self, 
        feedback_id: str,
        user_id: str,
        text: str,
        metadata: Dict
    ):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            embedding = self.create_embedding(text)
            
            cur.execute("""
                INSERT INTO feedback_embeddings 
                (feedback_id, user_id, embedding, text, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                feedback_id,
                user_id,
                embedding,
                text,
                json.dumps(metadata)
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"Error saving feedback: {e}")
    
    def search_similar_feedbacks(
        self, 
        query_text: str, 
        user_id: str, 
        top_k: int = 5
    ) -> List[Dict]:
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            query_embedding = self.create_embedding(query_text)
            
            cur.execute("""
                SELECT text, metadata, 
                       embedding <=> %s::vector as distance
                FROM feedback_embeddings
                WHERE user_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, user_id, query_embedding, top_k))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "text": row[0],
                    "metadata": row[1],
                    "distance": float(row[2])
                })
            
            cur.close()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Error searching feedbacks: {e}")
            return []


class FeedbackParser:
    def __init__(self, openai_api_key: str | None = None):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
    
    def parse_feedback_to_preferences(self, user_text: str) -> Dict:
        prompt = f"""당신은 메이크업 추천을 위한 개인화 선호도 분석 AI입니다.

사용자의 피드백 문장을 읽고 다음 항목을 JSON으로 추출하세요:

- desired_tone: "warm" | "cool" | "neutral" | null
- depth: "lighter" | "deeper" | "similar" | null
- mood: ["mlbb", "rosy", "vivid", "soft", ...] (리스트)
- finish: ["matte", "glow", "cream", "satin", ...] (리스트)
- store_type: ["oliveyoung", "roadshop", "department", ...] (리스트)
- dislike_keywords: 사용자가 피하고 싶은 느낌이나 키워드 (리스트)

사용자 피드백: "{user_text}"

반드시 아래와 같은 JSON만 출력하세요:

{{
  "desired_tone": null,
  "depth": null,
  "mood": [],
  "finish": [],
  "store_type": [],
  "dislike_keywords": []
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strict JSON-only preference parser."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            raw = response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            parsed = json.loads(raw)
            return parsed
            
        except json.JSONDecodeError:
            return {
                "desired_tone": None,
                "depth": None,
                "mood": [],
                "finish": [],
                "store_type": [],
                "dislike_keywords": []
            }
        except Exception as e:
            print(f"Feedback parsing error: {e}")
            return {
                "desired_tone": None,
                "depth": None,
                "mood": [],
                "finish": [],
                "store_type": [],
                "dislike_keywords": []
            }


class ProductReranker:
    def score_product(
        self, 
        product: Dict, 
        parsed_pref: Dict, 
        user_profile: Dict
    ) -> float:
        score = 0.0
        
        if "deltaE" in product:
            dE = product["deltaE"]
            color_score = max(0, 1 - dE / 20)
            score += 0.5 * color_score
        
        preferred_finish = parsed_pref.get("finish", [])
        if preferred_finish and product.get("finish"):
            finish_map = {
                "matte": "matte",
                "glossy": "glow",
                "glow": "glow",
                "satin": "satin",
                "cream": "cream"
            }
            product_finish = finish_map.get(product["finish"].lower(), product["finish"].lower())
            if product_finish in [f.lower() for f in preferred_finish]:
                score += 0.2
        
        depth = parsed_pref.get("depth")
        if depth and "deltaE" in product:
            if depth == "similar" and product["deltaE"] < 5:
                score += 0.1
            elif depth == "deeper":
                score += 0.1
            elif depth == "lighter":
                score += 0.1
        
        moods = parsed_pref.get("mood", [])
        product_name = product.get("product_name", "").lower()
        shade_name = product.get("shade_name", "").lower()
        combined_text = f"{product_name} {shade_name}"
        
        for mood in moods:
            if mood.lower() in combined_text:
                score += 0.1
        
        dislikes = parsed_pref.get("dislike_keywords", [])
        for dislike in dislikes:
            if dislike.lower() in combined_text:
                score -= 0.3
        
        return score
    
    def rerank_products(
        self, 
        candidates: List[Dict], 
        parsed_pref: Dict, 
        user_profile: Dict
    ) -> List[Dict]:
        scored = []
        for product in candidates:
            score = self.score_product(product, parsed_pref, user_profile)
            scored.append((score, product))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for s, p in scored[:3]]


class RAGAgent:
    def __init__(
        self, 
        vector_db: VectorDB,
        feedback_parser: FeedbackParser,
        reranker: ProductReranker,
        openai_api_key: str | None = None
    ):
        self.vector_db = vector_db
        self.feedback_parser = feedback_parser
        self.reranker = reranker
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
    
    def generate_explanation(self, products: List[Dict], category: str) -> List[str]:
        if not products:
            return []
        
        category_kr = {"lips": "립", "cheeks": "치크", "eyes": "아이섀도우"}.get(category, "메이크업")
        
        prompt = f"""당신은 K-뷰티 메이크업 전문가입니다.

아래 Top3 {category_kr} 제품의 추천 이유를 각각 2문장으로 간결하게 작성하세요.

제품 정보:
"""
        
        for rank, prod in enumerate(products, start=1):
            prompt += f"""
{rank}위: {prod['brand']} {prod['product_name']}
"""
        
        prompt += """
규칙:
1) 각 제품당 정확히 2문장
2) 사용자 피드백을 반영했다는 점 강조
3) MLBB/rosy/warm/cool/데일리 등 감성 단어 사용
4) 아래 JSON만 출력

{
  "reasons": [
    "1위 추천 이유",
    "2위 추천 이유",
    "3위 추천 이유"
  ]
}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional beauty analyst. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            raw = response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(raw)
            reasons = data.get("reasons", [])
            
            while len(reasons) < len(products):
                reasons.append("피드백을 반영해 추천된 제품입니다.")
            
            return reasons[:len(products)]
            
        except Exception:
            return ["피드백을 반영해 추천된 제품입니다."] * len(products)
    
    def process_message(
        self,
        user_id: str,
        message: str,
        current_recommendations: List[Dict],
        user_profile: Dict,
        category: str
    ) -> Dict:
        parsed_pref = self.feedback_parser.parse_feedback_to_preferences(message)
        
        import uuid
        feedback_id = str(uuid.uuid4())
        self.vector_db.save_feedback(
            feedback_id=feedback_id,
            user_id=user_id,
            text=message,
            metadata={
                "preferences": parsed_pref,
                "category": category,
                "timestamp": str(uuid.uuid1())
            }
        )
        
        similar_feedbacks = self.vector_db.search_similar_feedbacks(message, user_id, top_k=3)
        
        results = self.reranker.rerank_products(
            current_recommendations, 
            parsed_pref, 
            user_profile
        )
        
        reasons = self.generate_explanation(results, category)
        
        for i, product in enumerate(results):
            product["reason"] = reasons[i] if i < len(reasons) else "피드백을 반영해 추천된 제품입니다."
        
        return {
            "agent_message": "피드백 반영해서 다시 골라봤어요!",
            "parsed_preferences": parsed_pref,
            "similar_past_feedbacks": similar_feedbacks,
            "results": results
        }