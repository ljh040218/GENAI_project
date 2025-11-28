import os
import json
import psycopg2
from typing import Dict, List, Tuple, Optional, Any
from openai import OpenAI
import numpy as np
import logging
import uuid # UUID 생성을 위해 추가

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self):
        # 두 개의 DB URL을 환경변수에서 로드
        self.vector_db_url = os.getenv("VECTOR_DATABASE_URL")
        self.general_db_url = os.getenv("DATABASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.vector_db_url or not self.general_db_url:
            raise ValueError("데이터베이스 URL(VECTOR_DATABASE_URL, DATABASE_URL)이 설정되지 않았습니다.")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
            
        self.client = OpenAI(api_key=self.api_key)
    
    def get_vector_connection(self):
        """네온(Vector) DB 연결"""
        return psycopg2.connect(self.vector_db_url)

    def get_general_connection(self):
        """일반(PostgreSQL) DB 연결"""
        return psycopg2.connect(self.general_db_url)
    
    def create_embedding(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            return [0.0] * 1536  # 실패 시 0 벡터 반환

    def save_feedback(self, feedback_id: str, user_id: str, text: str, metadata: Dict):
        """사용자 피드백(채팅) 저장"""
        try:
            conn = self.get_vector_connection()
            cur = conn.cursor()
            
            embedding = self.create_embedding(text)
            
            # JSON 메타데이터 직렬화
            import json
            metadata_json = json.dumps(metadata)
            
            cur.execute("""
                INSERT INTO feedback_embeddings 
                (feedback_id, user_id, embedding, text, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (feedback_id, user_id, embedding, text, metadata_json))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Feedback save failed: {e}")

    def search_similar_feedbacks(self, query_text: str, user_id: str, top_k: int = 3) -> List[Dict]:
        """과거 대화 맥락 검색"""
        try:
            conn = self.get_vector_connection()
            cur = conn.cursor()
            
            query_embedding = self.create_embedding(query_text)
            
            cur.execute("""
                SELECT text, metadata, embedding <=> %s::vector as distance
                FROM feedback_embeddings
                WHERE user_id = %s
                ORDER BY distance ASC
                LIMIT %s
            """, (query_embedding, user_id, top_k))
            
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
            logger.error(f"Feedback search failed: {e}")
            return []

    def search_products(self, query_text: str, category: str, top_k: int = 5) -> List[Dict]:
        """제품 검색 (Semantic Search)"""
        try:
            conn = self.get_vector_connection()
            cur = conn.cursor()
            
            query_embedding = self.create_embedding(query_text)
            
            # 카테고리가 일치하는 제품 중에서 의미적 유사도 검색
            cur.execute("""
                SELECT brand, product_name, color_name, price, text, metadata,
                       embedding <=> %s::vector as distance
                FROM product_embeddings
                WHERE category = %s
                ORDER BY distance ASC
                LIMIT %s
            """, (query_embedding, category, top_k))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "brand": row[0],
                    "product_name": row[1],
                    "shade_name": row[2],
                    "price": row[3],
                    "text": row[4],       # rag_text
                    "metadata": row[5],
                    "distance": float(row[6]),
                    "finish": row[5].get("finish", "unknown") if row[5] else "unknown"
                })
            
            cur.close()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []


class IntentClassifier:
    def classify(self, message: str) -> str:
        # 간단한 키워드 기반 분류 (실제로는 LLM이나 별도 모델 사용 권장)
        if any(word in message for word in ["왜", "이유", "설명"]):
            return "explain"
        elif any(word in message for word in ["유행", "트렌드", "인기"]):
            return "trend"
        elif any(word in message for word in ["추천", "찾아줘", "골라줘", "어때"]):
            return "recommend"
        else:
            return "both" # 기본값


class FeedbackParser:
    def parse_feedback_to_preferences(self, message: str) -> Dict:
        # 간단한 파싱 로직
        preferences = {
            "tone": "unknown",
            "finish": "unknown",
            "brightness": "unknown",
            "saturation": "unknown",
            "like_keywords": [],
            "dislike_keywords": [],
            "brand": ""
        }
        
        # 키워드 추출 예시
        if "쿨톤" in message: preferences["tone"] = "cool"
        if "웜톤" in message: preferences["tone"] = "warm"
        if "매트" in message: preferences["finish"] = "matte"
        if "촉촉" in message or "글로시" in message: preferences["finish"] = "glossy"
        
        # 명사 추출 로직 대신 간단히 전체 메시지를 키워드로 활용하거나
        # 형태소 분석기를 붙일 수 있음. 여기서는 메시지 자체를 검색 쿼리로 활용.
        preferences["like_keywords"].append(message) 
        
        return preferences


class ProductReranker:
    def rerank_products(self, candidates: List[Dict], parsed_pref: Dict, user_profile: Dict, top_k: int = 3):
        # 간단한 점수 로직 (실제로는 복잡한 알고리즘 가능)
        scored_candidates = []
        
        for p in candidates:
            score = 0.0
            
            # 1. 텍스트 검색 유사도 (이미 DB에서 계산됨, 거리니까 역수 취급하거나 -distance)
            if "distance" in p:
                score += (1.0 - p["distance"]) * 50  # 가중치 50
            
            # 2. 프로필 매칭 (톤)
            p_meta = p.get("metadata", {})
            p_tone = p_meta.get("tone", "") if p_meta else ""
            u_tone = user_profile.get("tone", "")
            
            if u_tone and p_tone and (u_tone in p_tone or p_tone in u_tone):
                score += 30
            
            # 3. 선호 제형
            p_finish = p.get("finish", "")
            u_finish = parsed_pref.get("finish", "")
            if u_finish and p_finish and u_finish == p_finish:
                score += 20
                
            scored_candidates.append((score, p))
            
        # 점수 내림차순 정렬
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # 상위 k개 반환
        final_list = [item[1] for item in scored_candidates[:top_k]]
        
        # 여기서는 text_based와 profile_based를 단순히 동일하게 반환하거나 나누어 반환 가능
        # 편의상 동일하게 반환
        return final_list, final_list


class RAGAgent:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.intent_classifier = IntentClassifier()
        self.feedback_parser = FeedbackParser()
        self.reranker = ProductReranker()
        
        # LLM 클라이언트 (VectorDB에 있는거 재사용하거나 새로 생성)
        self.client = self.vector_db.client

    def process_message(
        self,
        user_id: str,
        message: str,
        current_recommendations: List[Dict],
        user_profile: Dict,
        category: str
    ) -> Dict:
        # 1. 의도 파악
        intent = self.intent_classifier.classify(message)
        
        # 2. 선호도 추출
        parsed_pref = self.feedback_parser.parse_feedback_to_preferences(message)
        
        # 3. 사용자 채팅 저장 (메모리)
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
        
        # 4. 관련 과거 대화 검색 (Context)
        similar_feedbacks = self.vector_db.search_similar_feedbacks(message, user_id, top_k=3)
        
        # (1) 단순 설명/트렌드 질문
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
        
        # (2) 제품 추천 요청 (recommend or both)
        # 검색 쿼리 확장
        search_query = f"{message} {' '.join(parsed_pref['like_keywords'])}"
        
        # [중요] 검색 개수 6개로 증가 (다양성 확보)
        db_products = self.vector_db.search_products(
            query_text=search_query, 
            category=category, 
            top_k=6 
        )
        
        # 후보군 병합 (DB검색 결과 + 현재 보고 있는 추천 목록)
        candidates = db_products 
        
        # 만약 DB 검색 결과가 적으면 기존 추천도 포함
        if len(candidates) < 2:
            # current_recommendations 형식이 DB형식과 다를 수 있어 변환 필요할 수 있음
            # 여기서는 단순 병합 시도 (에러 방지 위해 try-except 안쓰고 리스트만 합침)
            candidates.extend(current_recommendations)

        # 리랭킹
        text_based, profile_based = self.reranker.rerank_products(
            candidates, 
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

    def generate_explanation(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        memories: List[Dict],
        text_based: List[Dict],
        profile_based: List[Dict],
        web_context: Optional[str]
    ) -> Dict:
        
        # 프롬프트에 넣을 제품 목록 텍스트 생성
        candidates = text_based + profile_based
        
        # 중복 제거 (product_name 기준)
        seen = set()
        unique_candidates = []
        for p in candidates:
            name = p.get('product_name', '')
            if name and name not in seen:
                seen.add(name)
                unique_candidates.append(p)
        
        products_context = ""
        if unique_candidates:
            for idx, p in enumerate(unique_candidates):
                # rag_text가 있으면 쓰고, 없으면 기본 정보 조합
                desc = p.get('text', '')
                if not desc:
                    desc = f"{p.get('color_name', '')} 색상, {p.get('finish', '')} 피니시"
                
                products_context += f"""
                [제품 {idx+1}]
                - 브랜드: {p.get('brand', 'Unknown')}
                - 이름: {p.get('product_name', 'Unknown')} ({p.get('shade_name', p.get('color_name', ''))})
                - 가격: {p.get('price', 0)}원
                - 특징: {desc}
                """
        else:
            products_context = "검색된 적합한 제품이 없습니다."

        # ==========================================================
        # [수정된 시스템 프롬프트]
        # 변수명 오류 수정: {message} -> {user_text}
        # ==========================================================
        system_prompt = f"""
        당신은 융통성 있고 설득력 있는 K-Beauty AI 뷰티 컨설턴트입니다.
        
        [사용자 프로필]
        - 퍼스널 컬러: {user_profile.get('tone', '알 수 없음')}
        - 선호 브랜드: {', '.join(user_profile.get('fav_brands', []))}
        - 선호 피니시: {', '.join(user_profile.get('finish_preference', []))}
        
        [검색된 후보 제품 목록]
        {products_context}
        
        [사용자 질문]
        "{user_text}"
        
        [필수 지시사항 (반드시 따를 것)]
        1. **무조건 하나 이상의 제품을 추천하세요.** 완벽한 조건(가격, 톤 등)에 맞는 제품이 없더라도, 후보 제품 중 가장 근접한 제품을 선택하세요.
        
        2. **'톤 크로스(Tone-Cross)' 추천을 허용합니다.**
           - 만약 사용자는 '여쿨'인데 검색된 제품이 '웜톤'용이라면, 추천을 포기하지 말고 다음과 같이 설득하세요:
           - 예시: "고객님은 여름 쿨톤이시지만, 이 제품은 맑게 발색되어 웜톤 컬러임에도 고객님께 분위기 있게 어우러질 수 있어 추천드려요."
           - 예시: "원하시는 매트 제형은 아니지만, 이 제품은 세미-글로우라서 부담스럽지 않게 사용하실 수 있어요."
        
        3. **추천 근거를 구체적으로 제시하세요.**
           - 제품의 특징(rag_text)을 인용해서 "이 제품의 OO 성분이~", "리뷰에서 OO라고 해서~" 라고 말하세요.
           
        4. 없는 제품을 지어내지는 마세요. 반드시 [검색된 후보 제품 목록] 안에 있는 것 중에서만 고르세요.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7
            )
            assistant_message = response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            assistant_message = "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다."

        return {
            "assistant_message": assistant_message,
            "user_text_based": text_based,
            "user_profile_based": profile_based,
            "parsed_preferences": parsed_pref,
            "intent": "processed"
        }