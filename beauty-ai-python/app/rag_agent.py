import os
import json
import psycopg2
from typing import Dict, List, Tuple, Optional, Any
from openai import OpenAI
import numpy as np
import logging

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
            return []
    
    def save_feedback(self, feedback_id: str, user_id: str, text: str, metadata: Dict):
        """사용자 피드백(채팅) 저장"""
        try:
            conn = self.get_vector_connection()
            cur = conn.cursor()
            embedding = self.create_embedding(text)
            
            cur.execute("""
                INSERT INTO feedback_embeddings 
                (feedback_id, user_id, embedding, text, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (feedback_id, user_id, embedding, text, json.dumps(metadata)))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Save feedback failed: {e}")

    def search_similar_feedbacks(self, query_text: str, user_id: str, top_k: int = 3) -> List[Dict]:
        """과거 대화 검색"""
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
            logger.error(f"Search feedbacks failed: {e}")
            return []

    def search_products(self, query_text: str, category: str, top_k: int = 5) -> List[Dict]:
        """
        [핵심] 벡터 DB에서 의미 기반 제품 검색
        """
        try:
            conn = self.get_vector_connection()
            cur = conn.cursor()
            query_embedding = self.create_embedding(query_text)
            
            # 카테고리 매핑 (프론트엔드 값 -> DB 값)
            # 예: 'lip' -> 'lips' (DB에 저장된 형태에 따라 조정 필요)
            category_map = {"lip": "lips", "eye": "eyes", "cheek": "cheeks"}
            db_category = category_map.get(category, category)

            # 벡터 유사도 검색 (L2 Distance)
            cur.execute("""
                SELECT id, product_id, brand, product_name, color_name, price, text, metadata, 
                       embedding <=> %s::vector as distance
                FROM product_embeddings
                WHERE category = %s
                ORDER BY distance ASC
                LIMIT %s
            """, (query_embedding, db_category, top_k))
            
            vector_results = []
            for row in cur.fetchall():
                vector_results.append({
                    "vector_uuid": str(row[0]),
                    "product_id": str(row[1]), # 일반 DB와 연결할 Key
                    "brand": row[2],
                    "product_name": row[3],
                    "shade_name": row[4],
                    "price": row[5],
                    "rag_text": row[6], # 검색된 텍스트 원문
                    "metadata": row[7],
                    "distance": float(row[8])
                })
            
            cur.close()
            conn.close()
            
            # 검색 결과가 없으면 빈 리스트 반환
            if not vector_results:
                return []

            # [교차 검증] 일반 DB에서 최신 정보(가격, 존재여부) 확인
            return self.verify_with_general_db(vector_results)
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []

    def verify_with_general_db(self, vector_results: List[Dict]) -> List[Dict]:
        """
        [교차 검증] 벡터 DB에서 찾은 제품이 일반 DB에 실제로 있는지 확인하고 정보 보정
        """
        try:
            conn = self.get_general_connection()
            cur = conn.cursor()
            
            # product_id 목록 추출
            # product_id가 일반 DB의 id 컬럼(INT or String)과 타입이 맞아야 함
            ids = [item['product_id'] for item in vector_results]
            
            if not ids:
                return vector_results

            # 일반 DB 조회 (최신 가격 확인용)
            # 만약 일반 DB의 ID가 정수형(INT)이라면 형변환 주의
            format_strings = ','.join(['%s'] * len(ids))
            cur.execute(f"SELECT id, price, name, image_url FROM products WHERE id IN ({format_strings})", tuple(ids))
            
            real_products = {str(row[0]): {"price": row[1], "name": row[2], "image_url": row[3]} for row in cur.fetchall()}
            
            verified_results = []
            for item in vector_results:
                pid = item['product_id']
                if pid in real_products:
                    # 일반 DB에 존재하는 제품만 리스트에 추가 (할루시네이션 방지)
                    # 가격 정보를 최신으로 업데이트
                    item['price'] = real_products[pid]['price']
                    item['image_url'] = real_products[pid]['image_url']
                    verified_results.append(item)
            
            cur.close()
            conn.close()
            return verified_results

        except Exception as e:
            logger.error(f"General DB verification failed: {e}")
            # 일반 DB 연결 실패 시 벡터 DB 결과라도 반환 (장애 대응)
            return vector_results


class IntentClassifier:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client

    def classify(self, message: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Analyze the user's intent. Return only one of: 'recommend' (wants product suggestion), 'explain' (asks why/how), 'trend' (asks for popularity), 'chat' (general talk)."},
                    {"role": "user", "content": message}
                ],
                temperature=0.3
            )
            intent = response.choices[0].message.content.strip().lower()
            return intent if intent in ['recommend', 'explain', 'trend'] else 'recommend'
        except:
            return "recommend"


class FeedbackParser:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client

    def parse_feedback_to_preferences(self, message: str) -> Dict:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                    Extract beauty preferences from the user message.
                    Return JSON format:
                    {
                        "tone": "warm" | "cool" | "neutral" | "unknown",
                        "finish": "matte" | "glossy" | "satin" | "unknown",
                        "like_keywords": ["keyword1", "keyword2"],
                        "dislike_keywords": ["keyword1", "keyword2"]
                    }
                    """},
                    {"role": "user", "content": message}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except:
            return {"tone": "unknown", "finish": "unknown", "like_keywords": [], "dislike_keywords": []}


class ProductReranker:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client

    def rerank_products(self, candidates: List[Dict], user_pref: Dict, user_profile: Dict, top_k: int = 3):
        # 여기서는 간단히 필터링만 수행하거나 그대로 반환
        # 복잡한 로직은 VectorDB 검색 단계에서 이미 수행됨
        return candidates[:top_k], candidates[:top_k]


class RAGAgent:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.client = vector_db.client
        self.intent_classifier = IntentClassifier(self.client)
        self.feedback_parser = FeedbackParser(self.client)
        self.reranker = ProductReranker(self.client)

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
        
        # 3. 채팅 내용 저장 (Memory)
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
        
        # 4. 과거 대화 맥락 검색 (Context)
        similar_feedbacks = self.vector_db.search_similar_feedbacks(message, user_id, top_k=3)
        
        # ==========================================================
        # [핵심 로직] Intent에 따른 RAG 처리
        # ==========================================================
        
        retrieved_products = []
        
        # 추천이 필요한 경우 DB 검색 수행
        if intent in ['recommend', 'trend'] or (intent == 'explain' and not current_recommendations):
            # 검색어 생성: 사용자 질문 + 추출된 키워드
            search_query = f"{message} {' '.join(parsed_pref['like_keywords'])}"
            if user_profile.get('tone'):
                search_query += f" {user_profile['tone']}"
            
            # DB 검색 (Vector -> General 검증)
            retrieved_products = self.vector_db.search_products(search_query, category, top_k=5)
        
        # 기존 추천 제품과 새로 검색된 제품 병합 (중복 제거)
        final_candidates = retrieved_products
        
        # 답변 생성
        response_text = self.generate_response(
            message, 
            user_profile, 
            final_candidates, 
            similar_feedbacks,
            intent
        )
        
        return {
            "success": True,
            "assistant_message": response_text,
            "user_text_based": final_candidates, # 디버깅용
            "user_profile_based": final_candidates,
            "parsed_preferences": parsed_pref,
            "intent": intent
        }

    def generate_response(
        self, 
        user_text: str, 
        profile: Dict, 
        products: List[Dict], 
        memories: List[Dict],
        intent: str
    ) -> str:
        """
        검색된 제품 정보를 바탕으로 답변 생성 (Hallucination 방지 프롬프트 적용)
        """
        
        # 제품 정보를 문자열로 변환 (프롬프트 주입용)
        products_context = ""
        if products:
            for idx, p in enumerate(products):
                products_context += f"""
                [제품 {idx+1}]
                - 브랜드: {p['brand']}
                - 이름: {p['product_name']} ({p['shade_name']})
                - 가격: {p['price']}원
                - 특징: {p['rag_text']}
                """
        else:
            products_context = "검색된 적합한 제품이 없습니다."

        system_prompt = f"""
        당신은 K-Beauty 퍼스널 컬러 전문 AI 컨설턴트입니다.
        
        [사용자 프로필]
        - 톤: {profile.get('tone', '알 수 없음')}
        - 선호 브랜드: {', '.join(profile.get('fav_brands', []))}
        - 선호 피니시: {', '.join(profile.get('finish_preference', []))}
        
        [검색된 제품 목록 (DB 데이터)]
        {products_context}
        
        [과거 대화 기억]
        {[m['text'] for m in memories]}
        
        [지시사항]
        1. 반드시 위 [검색된 제품 목록]에 있는 제품 중에서만 추천하세요. **없는 제품을 지어내지 마세요.**
        2. 사용자의 질문("{user_text}")에 답변하되, 왜 이 제품이 사용자의 프로필(톤, 취향)에 맞는지 논리적으로 설명하세요.
        3. 제품이 검색되지 않았다면 솔직하게 "원하시는 조건에 딱 맞는 제품을 찾지 못했어요"라고 말하고 대안을 물어보세요.
        4. 어조는 친절하고 전문적인 뷰티 컨설턴트처럼 하세요.
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
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return "죄송합니다. 답변을 생성하는 도중 오류가 발생했습니다."