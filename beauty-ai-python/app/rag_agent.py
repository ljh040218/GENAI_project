import os
import json
import psycopg2
from typing import Dict, List, Tuple, Optional, Any
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


class IntentClassifier:
    def __init__(self, openai_api_key: str | None = None):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
    
    def classify(self, user_text: str) -> str:
        text = user_text.strip()
        
        recommend_keywords = ["추천", "골라줘", "골라 줄", "뭐가 나을까", "어떤 게 나을까", "바꾸고 싶어요", "바꿔줄래", "골라봐"]
        explain_keywords = ["뭐야", "뭐에요", "뭐예요", "차이", "설명해줘", "알려줘"]
        trend_keywords = ["트렌드", "유행", "요즘", "올해", "2026", "신상", "셀럽", "아이돌", "무대 메이크업"]
        
        if any(k in text for k in recommend_keywords):
            if any(k in text for k in explain_keywords) or any(k in text for k in trend_keywords):
                return "both"
            return "recommend"
        
        if any(k in text for k in trend_keywords):
            return "trend"
        
        if any(k in text for k in explain_keywords):
            return "explain"
        
        prompt = f"""
너는 뷰티 AI Assistant의 인텐트 분석기야.

아래 사용자 문장을 보고 intent를 다음 중 하나로 분류해:

1) "recommend": 제품 추천이 핵심
2) "explain": 색조 이론/톤/개념 설명만 필요
3) "trend": 최신 정보, 시즌 트렌드, 셀럽 메이크업 질문
4) "both": 설명+추천이 섞인 경우

반드시 아래 JSON만 출력:
{{
  "intent": "recommend"
}}

분석할 문장:
"{user_text}"
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You must output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=80
            )
            
            raw = response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(raw)
            intent = data.get("intent", "recommend")
            
            if intent not in ["recommend", "explain", "trend", "both"]:
                intent = "recommend"
            
            return intent
            
        except Exception:
            return "recommend"


class FeedbackParser:
    def __init__(self, openai_api_key: str | None = None):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
    
    def parse_feedback_to_preferences(self, user_text: str) -> Dict[str, Any]:
        prompt = f"""
너는 K-뷰티 색조 분석가야.

사용자 문장에서 취향 정보를 JSON으로 추출해줘.

사용자 문장:
"{user_text}"

JSON 형식:
{{
  "tone": "cool / warm / neutral / unknown 중 하나",
  "finish": "glossy / matte / velvet / tint / unknown 중 하나",
  "brightness": "밝음 / 중간 / 어두움 / unknown 중 하나",
  "saturation": "선명 / 은은 / 뮤트 / unknown 중 하나",
  "like_keywords": ["사용자가 선호한다고 언급한 키워드 목록"],
  "dislike_keywords": ["사용자가 피하고 싶다고 한 키워드 목록"],
  "brand": "언급한 브랜드가 있으면 적어, 없으면 빈 문자열"
}}

반드시 위 JSON 형식만 출력해.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You must output ONLY valid JSON with the specified keys.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            
            raw = response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(raw)
            except Exception:
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1:
                    data = json.loads(raw[start : end + 1])
                else:
                    data = {}
            
            return {
                "tone": data.get("tone", "unknown"),
                "finish": data.get("finish", "unknown"),
                "brightness": data.get("brightness", "unknown"),
                "saturation": data.get("saturation", "unknown"),
                "like_keywords": data.get("like_keywords", []),
                "dislike_keywords": data.get("dislike_keywords", []),
                "brand": data.get("brand", "")
            }
            
        except Exception as e:
            print(f"Feedback parsing error: {e}")
            return {
                "tone": "unknown",
                "finish": "unknown",
                "brightness": "unknown",
                "saturation": "unknown",
                "like_keywords": [],
                "dislike_keywords": [],
                "brand": ""
            }


class ProductReranker:
    def score_product_text_based(
        self, 
        product: Dict, 
        parsed_pref: Dict, 
        user_profile: Dict
    ) -> float:
        score = 0.0
        
        if "deltaE" in product:
            dE = product["deltaE"]
            color_score = (10 - min(dE, 10)) * 0.5
            score += color_score
        
        finish = (product.get("finish", "")).lower()
        parsed_finish = parsed_pref.get("finish", "unknown").lower()
        
        if parsed_finish != "unknown" and parsed_finish in finish:
            score += 2.5
        
        moods = parsed_pref.get("like_keywords", [])
        product_name = product.get("product_name", "").lower()
        shade_name = product.get("shade_name", "").lower()
        combined_text = f"{product_name} {shade_name}"
        
        for mood in moods:
            if mood.lower() in combined_text:
                score += 2.0
        
        dislikes = parsed_pref.get("dislike_keywords", [])
        for dislike in dislikes:
            if dislike.lower() in combined_text:
                score -= 3.0
        
        if parsed_pref.get("brand") and parsed_pref["brand"] in product.get("brand", ""):
            score += 1.5
        
        return score
    
    def score_product_profile_based(
        self, 
        product: Dict, 
        parsed_pref: Dict, 
        user_profile: Dict
    ) -> float:
        score = 0.0
        
        if "deltaE" in product:
            dE = product["deltaE"]
            color_score = (10 - min(dE, 10)) * 0.5
            score += color_score
        
        finish = (product.get("finish", "")).lower()
        
        if finish in [f.lower() for f in user_profile.get("finish_preference", [])]:
            score += 2.5
        
        if product.get("brand") in user_profile.get("fav_brands", []):
            score += 1.5
        
        for avoid in user_profile.get("avoid", []):
            combined_text = f"{product.get('product_name', '')} {product.get('shade_name', '')}".lower()
            if avoid.lower() in combined_text:
                score -= 2.0
        
        return score
    
    def rerank_products(
        self, 
        candidates: List[Dict], 
        parsed_pref: Dict, 
        user_profile: Dict,
        top_k: int = 3
    ) -> Tuple[List[Dict], List[Dict]]:
        scored_text = [
            (self.score_product_text_based(p, parsed_pref, user_profile), p)
            for p in candidates
        ]
        scored_text.sort(key=lambda x: x[0], reverse=True)
        text_based = [p for s, p in scored_text[:top_k]]
        
        scored_profile = [
            (self.score_product_profile_based(p, parsed_pref, user_profile), p)
            for p in candidates
        ]
        scored_profile.sort(key=lambda x: x[0], reverse=True)
        profile_based = [p for s, p in scored_profile[:top_k]]
        
        return text_based, profile_based


class RAGAgent:
    def __init__(
        self, 
        vector_db: VectorDB,
        intent_classifier: IntentClassifier,
        feedback_parser: FeedbackParser,
        reranker: ProductReranker,
        openai_api_key: str | None = None
    ):
        self.vector_db = vector_db
        self.intent_classifier = intent_classifier
        self.feedback_parser = feedback_parser
        self.reranker = reranker
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
    
    def format_product_list(self, products: List[Dict]) -> str:
        if not products:
            return "없음"
        
        lines = []
        for i, p in enumerate(products, start=1):
            line = (
                f"{i}번) {p.get('brand','')} {p.get('product_name','')} "
                f"{p.get('shade_name','')}"
                f" / 피니쉬: {p.get('finish','')}"
                f" / ΔE: {p.get('deltaE',0):.2f}"
            )
            lines.append(line)
        return "\n".join(lines)
    
    def generate_explanation(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        memories: List[Dict],
        text_based: List[Dict],
        profile_based: List[Dict],
        web_context: str | None = None
    ) -> Dict[str, Any]:
        history_snippets = [m.get("text", "") for m in memories[-3:]]
        history_text = "\n".join(history_snippets) if history_snippets else "이전 대화 없음"
        
        text_rec_block = self.format_product_list(text_based)
        profile_rec_block = self.format_product_list(profile_based)
        
        profile_summary = ", ".join(
            f"{k}={v}" for k, v in user_profile.items()
        ) if user_profile else "정보 없음"
        
        web_block = web_context if web_context else "없음"
        
        prompt = f"""
너는 K-뷰티 AI Beauty Assistant야.

[사용자 질문]
{user_text}

[사용자 프로필]
{profile_summary}

[추출된 선호(pref)]
{json.dumps(parsed_pref, ensure_ascii=False)}

[이전 대화 요약]
{history_text}

[사용자 피드백 기반 재추천 후보(user_text_based)]
{text_rec_block}

[사용자 프로필 기반 재추천 후보(user_profile_based)]
{profile_rec_block}

[웹 검색/트렌드 정보(web_context)]
{web_block}

위 정보를 참고해서 다음 규칙을 따라서 답변을 출력해.

규칙:
1) 반드시 한국어로 답변합니다.
2) 답변은 하나의 긴 메시지로 작성하되, 다음 구조를 따릅니다.
   - 1단락: 사용자의 요청과 상황을 공감하며 요약
   - 2단락: [사용자 피드백 기반 재추천] 제품 1~3개 이름과 그 이유 설명
   - 3단락: [사용자 프로필 기반 재추천] 제품 1~3개 이름과 그 이유 설명
   - (필요하다면) 4단락: 웹/트렌드 정보가 있을 경우, 관련된 팁이나 설명 추가
3) 제품을 언급할 때는 브랜드 + 제품명 + 쉐이드명을 꼭 포함하세요.
4) 존재하지 않는 제품이나 우리가 제공하지 않은 정보(지속력, 성분 등)는 만들어내지 마세요.
5) 자연스러운 문장으로 출력하세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise K-beauty assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1000,
            )
            
            assistant_message = response.choices[0].message.content.strip()
            
            return {
                "assistant_message": assistant_message,
                "user_text_based": text_based,
                "user_profile_based": profile_based,
                "parsed_preferences": parsed_pref,
                "intent": "processed"
            }
            
        except Exception as e:
            print(f"Generation error: {e}")
            return {
                "assistant_message": "죄송합니다. 응답 생성 중 오류가 발생했습니다.",
                "user_text_based": text_based,
                "user_profile_based": profile_based,
                "parsed_preferences": parsed_pref,
                "intent": "error"
            }
    
    def process_message(
        self,
        user_id: str,
        message: str,
        current_recommendations: List[Dict],
        user_profile: Dict,
        category: str
    ) -> Dict:
        intent = self.intent_classifier.classify(message)
        
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
                "intent": intent,
                "timestamp": str(uuid.uuid1())
            }
        )
        
        similar_feedbacks = self.vector_db.search_similar_feedbacks(message, user_id, top_k=3)
        
        if intent == "explain":
            return self.generate_explanation(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                memories=similar_feedbacks,
                text_based=[],
                profile_based=[],
                web_context=None
            )
        
        if intent == "trend":
            return self.generate_explanation(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                memories=similar_feedbacks,
                text_based=[],
                profile_based=[],
                web_context="최신 트렌드 정보는 웹 검색을 통해 제공될 예정입니다."
            )
        
        text_based, profile_based = self.reranker.rerank_products(
            current_recommendations, 
            parsed_pref, 
            user_profile,
            top_k=3
        )
        
        return self.generate_explanation(
            user_text=message,
            user_profile=user_profile,
            parsed_pref=parsed_pref,
            memories=similar_feedbacks,
            text_based=text_based,
            profile_based=profile_based,
            web_context=None
        )