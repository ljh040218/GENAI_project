import os
import json
import psycopg2
from typing import Dict, List, Tuple, Optional, Any
from openai import OpenAI
import numpy as np
import uuid
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self):
        # 환경변수에서 로드 (인자 제거)
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
            logger.error(f"Feedback save failed: {e}")

    def search_similar_feedbacks(self, query_text: str, user_id: str, top_k: int = 3) -> List[Dict]:
        """유사한 과거 대화 검색"""
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
        [핵심] 제품 벡터 DB 검색
        """
        try:
            conn = self.get_vector_connection()
            cur = conn.cursor()
            
            # 사용자의 불만/요구를 벡터로 변환
            query_embedding = self.create_embedding(query_text)
            
            # 의미적으로 가장 가까운 제품 검색 (Cosine Distance)
            # category가 일치하는 것 중에서 찾음
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
                # metadata가 None인 경우를 대비해 빈 딕셔너리 처리
                meta = row[5] if row[5] else {}
                
                results.append({
                    "brand": row[0],
                    "product_name": row[1],
                    "shade_name": row[2],
                    "price": row[3],
                    "rag_text": row[4], # DB에 저장된 '리뷰+특징' 텍스트 덩어리
                    "metadata": meta,
                    "distance": float(row[6]),
                    "finish": meta.get("texture", "unknown") # 텍스처 정보 추출
                })
            
            cur.close()
            conn.close()
            logger.info(f"🔍 [DB Search] Found {len(results)} products for query: '{query_text}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []


class IntentClassifier:
    def classify(self, text: str) -> str:
        # 간단한 키워드 기반 분류 (나중에 LLM으로 고도화 가능)
        if any(word in text for word in ["왜", "이유", "설명", "뭐야"]):
            return "explain"
        if any(word in text for word in ["유행", "트렌드", "요즘"]):
            return "trend"
        return "recommend"

class FeedbackParser:
    def parse_feedback_to_preferences(self, text: str) -> Dict:
        """사용자 채팅에서 선호/불호 키워드 추출 (간이 버전)"""
        preferences = {
            "tone": "unknown",
            "finish": "unknown",
            "like_keywords": [],
            "dislike_keywords": []
        }
        
        # 간단한 규칙 기반 파싱
        if "쿨톤" in text: preferences["tone"] = "cool"
        if "웜톤" in text: preferences["tone"] = "warm"
        if "매트" in text: preferences["finish"] = "matte"
        if "촉촉" in text or "글로시" in text: preferences["finish"] = "glossy"
        
        # 키워드 추출 (임베딩 검색 강화용)
        keywords = ["각질", "지속력", "발색", "착색", "매트", "촉촉", "광택", "보송", "세미매트"]
        for kw in keywords:
            if kw in text:
                preferences["like_keywords"].append(kw)
                
        return preferences

class RAGAgent:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.intent_classifier = IntentClassifier()
        self.feedback_parser = FeedbackParser()
        
        # OpenAI 클라이언트 (답변 생성용)
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

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
        
        # 3. 사용자 채팅 저장 (단기 기억용)
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
        
        # ------------------------------------------------------------------
        # [핵심 로직 수정] 엄격한 필터링 제거하고 DB 검색 결과를 신뢰함
        # ------------------------------------------------------------------
        
        # 검색 쿼리 확장: 사용자 질문 + 추출된 키워드
        search_query = f"{message} {' '.join(parsed_pref['like_keywords'])}"
        
        # [수정 1] 검색 개수(top_k)를 6개로 늘림 (후보군 확보)
        db_products = self.vector_db.search_products(
            query_text=search_query, 
            category=category, 
            top_k=6 
        )
        
        # [수정 2] 파이썬 필터링(Reranker) 제거 -> LLM에게 판단 위임
        # DB가 이미 '의미적으로' 가장 가까운걸 찾아왔으므로(예: 세미매트), 그대로 넘깁니다.
        final_candidates = db_products
        
        # 만약 DB 검색 결과가 너무 적으면(0개), 기존 추천 목록이라도 넣어서 대화가 끊기지 않게 함
        if not final_candidates and current_recommendations:
             # current_recommendations 형식을 db_products 형식으로 변환해야 함 (약식 처리)
             for item in current_recommendations:
                 final_candidates.append({
                     "brand": item.get("brand", ""),
                     "product_name": item.get("product_name", ""),
                     "shade_name": item.get("shade_name", ""),
                     "rag_text": f"{item.get('brand')} {item.get('product_name')}. 기존 추천 제품입니다.",
                     "price": item.get("price", 0)
                 })

        # 5. LLM 답변 생성
        return self.generate_explanation(
            user_text=message,
            user_profile=user_profile,
            parsed_pref=parsed_pref,
            memories=similar_feedbacks,
            candidate_products=final_candidates
        )

    def generate_explanation(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        memories: List[Dict],
        candidate_products: List[Dict]
    ) -> Dict:
        
        # 프롬프트에 넣을 제품 목록 텍스트 생성
        if candidate_products:
            products_context = "\n".join([
                f"""
                [제품 {idx+1}]
                - 브랜드: {p['brand']}
                - 이름: {p['product_name']} ({p['shade_name']})
                - 가격: {p['price']}원
                - 상세정보/리뷰요약: {p.get('rag_text', '정보 없음')}
                """ for idx, p in enumerate(candidate_products)
            ])
        else:
            products_context = "검색된 적합한 제품이 없습니다."

        # ------------------------------------------------------------------
        # [수정 3] 시스템 프롬프트: "중재자 모드" 강화
        # ------------------------------------------------------------------
        system_prompt = f"""
        당신은 융통성 있고 설득력 있는 K-Beauty AI 뷰티 에이전트입니다.
        단순히 정보를 나열하지 말고, 퍼스널 컬러 전문가처럼 사용자를 설득하세요.

        [사용자 프로필]
        - 퍼스널 컬러: {user_profile.get('tone', '알 수 없음')}
        - 선호 브랜드: {', '.join(user_profile.get('fav_brands', []))}
        - 선호 피니시: {', '.join(user_profile.get('finish_preference', []))}
        
        [검색된 후보 제품 목록 (DB 기반)]
        {products_context}
        
        [사용자 질문/불만]
        "{user_text}"
        
        [행동 지침 (매우 중요)]
        1. **'추천 불가'라고 말하지 마세요.** 후보 제품 목록 중에서 사용자의 요구사항(텍스처, 색감 등)에 **가장 근접한 1~3개**를 반드시 골라내세요.
        
        2. 사용자 프로필에는 기본적으로 {user_profile.tone}으로 설정되어 있습니다.  
        하지만 사용자가 대화 중 다음과 같은 의도를 보이면 ‘톤 크로스(Tone-Cross)’ 추천을 허용하세요:

        - "쿨톤 제품도 괜찮아요."
        - "웜톤이지만 쿨 느낌도 써보고 싶어요."
        - "톤 상관없이 예쁜 색 추천해줘."
        - "다른 톤도 제안해줘."

        톤 크로스 상황에서는 다음 원칙을 따르세요:

        1. **사용자가 원한 톤(예: 쿨톤)을 우선으로 추천합니다.**
        2. **단, 기존 사용자 프로필(예: 웜톤)과 다른 톤을 추천할 때는 반드시 왜 어울리는지를 설명하세요.**
           - 예: “고객님은 웜톤이지만 이 쿨 핑크는 채도가 낮고 약간 그레이시해서 웜톤도 데일리로 쓰기 좋아요!”
        3. **명도·채도·언더톤·텍스처를 근거로 설득력 있게 설명합니다.**
        4. **사용자가 Tone-Cross가 불편해한다면 즉시 기본 톤으로 되돌아갑니다.**

        이 규칙을 모든 추천 답변에서 항상 적용하세요.

        3. **근거를 제시하세요.**
           - 제품 정보(rag_text)에 있는 "각질 부각 없음", "지속력 좋음" 등의 멘트를 인용해서 추천 이유를 설명하세요.
           
        4. 답변은 친절하고 공감하는 말투(해요체)로 작성하세요.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7 # 창의성 약간 높임 (설득을 위해)
            )
            
            assistant_message = response.choices[0].message.content
            
            return {
                "assistant_message": assistant_message,
                "recommendations": candidate_products[:3], # 상위 3개 정보를 프론트에 전달
                "parsed_preferences": parsed_pref,
                "intent": "recommend"
            }
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                "assistant_message": "죄송합니다. 답변을 생성하는 중에 문제가 발생했어요.",
                "recommendations": [],
                "parsed_preferences": parsed_pref,
                "intent": "error"
            }