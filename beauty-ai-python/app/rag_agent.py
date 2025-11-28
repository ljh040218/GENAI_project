import os
import json
import psycopg2
from typing import Dict, List, Tuple, Optional, Any
from openai import OpenAI
import numpy as np
import uuid
import logging

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self):
        # 환경변수에서 로드
        self.vector_db_url = os.getenv("VECTOR_DATABASE_URL")
        self.general_db_url = os.getenv("DATABASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.vector_db_url or not self.general_db_url:
            raise ValueError("데이터베이스 URL(VECTOR_DATABASE_URL, DATABASE_URL)이 설정되지 않았습니다.")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
            
        self.client = OpenAI(api_key=self.api_key)
    
    def get_vector_connection(self):
        """Vector DB 연결"""
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
            
            query_embedding = self.create_embedding(query_text)
            
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
                meta = row[5] if row[5] else {}
                
                results.append({
                    "brand": row[0],
                    "product_name": row[1],
                    "shade_name": row[2],
                    "price": row[3],
                    "rag_text": row[4], 
                    "metadata": meta,
                    "distance": float(row[6]),
                    "finish": meta.get("texture", "unknown") 
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
        # [PDF 반영] 트렌드/유행 관련 키워드 -> 웹 검색 트리거
        trend_keywords = ["유행", "트렌드", "요즘", "지금 뜨는", "핫한", "인기", "신상"]
        if any(word in text for word in trend_keywords):
            return "trend"
            
        if any(word in text for word in ["왜", "이유", "설명", "뭐야", "알려줘"]):
            return "explain"
            
        return "recommend"

class FeedbackParser:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def parse_preference(self, user_text: str) -> Dict[str, Any]:
        """
        user_text에서 톤/피니쉬/밝기/채도/좋아하는 키워드/싫어하는 키워드 추출 (LLM 사용)
        """
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
          "dislike_keywords": ["사용자가 피하고 싶다고 한 키워드 목록"]
        }}
        
        반드시 위 JSON 형식만 출력해.
        """

        try:
            res = self.client.chat.completions.create(
                model="gpt-4o-mini",  # gpt-4.1-mini는 존재하지 않으므로 gpt-4o-mini 사용
                messages=[
                    {
                        "role": "system",
                        "content": "You must output ONLY valid JSON with the specified keys.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=200,
            )

            raw = res.choices[0].message.content.strip()
            
            # JSON 포맷팅 클린업 (```json ... ``` 제거)
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            try:
                data = json.loads(raw)
            except Exception:
                # 혹시 앞뒤 잡다한 텍스트가 섞였을 때 대비
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1:
                    try:
                        data = json.loads(raw[start : end + 1])
                    except Exception:
                        data = {}
                else:
                    data = {}

        except Exception as e:
            logger.error(f"Preference parsing failed: {e}")
            data = {}

        return {
            "tone": data.get("tone", "unknown"),
            "finish": data.get("finish", "unknown"),
            "brightness": data.get("brightness", "unknown"),
            "saturation": data.get("saturation", "unknown"),
            "like_keywords": data.get("like_keywords", []),
            "dislike_keywords": data.get("dislike_keywords", []),
        }

class RAGAgent:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.intent_classifier = IntentClassifier()
        
        # OpenAI 클라이언트 및 파서 초기화
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.feedback_parser = FeedbackParser(api_key=api_key)

    def perform_web_search(self, query: str) -> str:
        """
        [PDF 반영] 웹 검색 도구 (DuckDuckGo Search 활용)
        """
        if DDGS is None:
            return "웹 검색 라이브러리(duckduckgo-search)가 설치되지 않아 검색할 수 없습니다."

        try:
            logger.info(f"Web Searching for: {query}")
            
            # 검색 실행 (상위 3개 결과)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            
            if not results:
                return "검색 결과가 없습니다."
            
            # 검색 결과를 LLM이 읽기 좋은 텍스트로 변환
            context_text = "\n".join([
                f"- 제목: {r['title']}\n  내용: {r['body']}\n  링크: {r['href']}"
                for r in results
            ])
            return context_text
            
        except Exception as e:
            logger.error(f"Web Search Failed: {e}")
            return f"웹 검색 중 오류가 발생했습니다: {str(e)}"

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
        logger.info(f"🤖 User Intent: {intent}")
        
        # 2. 선호도 추출 (LLM 기반)
        parsed_pref = self.feedback_parser.parse_preference(message)
        logger.info(f"🧠 Parsed User Preference: {parsed_pref}")
        
        # 3. 사용자 채팅 저장
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
        
        # 4. 과거 대화 맥락 검색
        similar_feedbacks = self.vector_db.search_similar_feedbacks(message, user_id, top_k=3)
        
        # ==================================================================
        # [분기 처리] 트렌드 질문(웹검색) vs 제품 추천(DB검색)
        # ==================================================================
        
        if intent == "trend":
            # (A) 웹 검색 수행
            search_context = self.perform_web_search(message)
            
            # (B) 트렌드 답변 생성
            return self.generate_trend_response(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                search_context=search_context
            )
            
        else:
            # (A) 제품 추천 (기존 로직) - DB 검색
            # 검색 쿼리 확장: LLM이 추출한 키워드 활용
            like_keywords_str = " ".join(parsed_pref.get('like_keywords', []))
            search_query = f"{message} {like_keywords_str} {like_keywords_str}"
            
            # DB 검색 (top_k=10)
            db_products = self.vector_db.search_products(
                query_text=search_query, 
                category=category, 
                top_k=10 
            )
            
            # 재정렬 로직 (매트/글로시 우선순위)
            user_finish = parsed_pref.get("finish", "unknown")
            if user_finish in ["matte", "velvet"]:
                target_keywords = ["매트", "세미매트", "보송", "벨벳", "무광", "파우더리"]
                db_products.sort(
                    key=lambda x: any(k in x['rag_text'] for k in target_keywords), 
                    reverse=True
                )
            elif user_finish in ["glossy", "tint"]:
                target_keywords = ["글로시", "촉촉", "광택", "탕후루", "물막", "수분"]
                db_products.sort(
                    key=lambda x: any(k in x['rag_text'] for k in target_keywords), 
                    reverse=True
                )
            
            final_candidates = db_products[:5]
            
            # DB 결과가 없으면 기존 추천 사용
            if not final_candidates and current_recommendations:
                 for item in current_recommendations:
                     final_candidates.append({
                         "brand": item.get("brand", ""),
                         "product_name": item.get("product_name", ""),
                         "shade_name": item.get("shade_name", ""),
                         "rag_text": f"{item.get('brand')} {item.get('product_name')}. 기존 추천 제품입니다.",
                         "price": item.get("price", 0),
                         "finish": item.get("finish", "unknown")
                     })

            # (B) 추천 답변 생성
            return self.generate_explanation(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                memories=similar_feedbacks,
                candidate_products=final_candidates
            )

    def generate_trend_response(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        search_context: str
    ) -> Dict:
        """웹 검색 결과를 바탕으로 트렌드 정보를 설명하는 답변 생성"""
        
        system_prompt = f"""
        당신은 최신 K-Beauty 트렌드를 꿰뚫고 있는 뷰티 에디터입니다.
        제공된 [웹 검색 결과]를 바탕으로 사용자의 질문에 답변하세요.
        
        [사용자 프로필]
        - 톤: {user_profile.get('tone', '알 수 없음')}
        - 관심사: {user_text}
        
        [웹 검색 결과]
        {search_context}
        
        [지시사항]
        1. 검색 결과에서 공통적으로 언급되는 핵심 트렌드(색상, 제형, 브랜드 등)를 요약하세요.
        2. 사용자의 프로필(퍼스널 컬러 등)과 연관 지어 팁을 주세요. (예: "요즘 글로시 립이 유행인데, 고객님 같은 여쿨에겐 이런 핑크가 좋아요")
        3. 검색 정보가 부족하면 일반적인 최신 뷰티 상식으로 답변하되, 출처는 언급하지 마세요.
        4. 친절하고 전문적인 어조(해요체)를 사용하세요.
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
            return {
                "success": True,
                "intent": "trend",
                "assistant_message": response.choices[0].message.content,
                "recommendations": [], 
                "parsed_preferences": parsed_pref
            }
        except Exception as e:
            logger.error(f"Trend generation failed: {e}")
            return {
                "success": False,
                "intent": "error",
                "assistant_message": "최신 트렌드를 불러오는 데 실패했습니다.",
                "recommendations": [],
                "parsed_preferences": parsed_pref
            }

    def generate_explanation(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        memories: List[Dict],
        candidate_products: List[Dict]
    ) -> Dict:
        
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

        system_prompt = f"""
        당신은 융통성 있고 설득력 있는 K-Beauty AI 뷰티 에이전트입니다.
        단순히 정보를 나열하지 말고, 퍼스널 컬러 전문가처럼 사용자를 설득하세요.

        [사용자 프로필]
        - 퍼스널 컬러: {user_profile.get('tone', '알 수 없음')}
        - 선호 브랜드: {', '.join(user_profile.get('fav_brands', []))}
        - 선호 피니시: {', '.join(user_profile.get('finish_preference', []))}
        
        [현재 대화에서 파악된 사용자 의도]
        - 원하는 톤: {parsed_pref.get('tone')}
        - 원하는 피니시: {parsed_pref.get('finish')}
        - 선호 키워드: {', '.join(parsed_pref.get('like_keywords', []))}
        
        [검색된 후보 제품 목록 (DB 기반)]
        {products_context}
        
        [사용자 질문/불만]
        "{user_text}"
        
        [행동 지침 (매우 중요)]
        1. **'추천 불가'라고 말하지 마세요.** 후보 제품 목록 중에서 사용자의 요구사항(텍스처, 색감 등)에 **가장 근접한 1~3개**를 반드시 골라내세요.
        
        2. **'톤 크로스(Tone-Cross)'와 '유사 속성'을 허용하세요.**
           - 사용자가 '매트'를 원하는데 검색 결과에 '세미매트'나 '벨벳'만 있다면? -> "완전한 매트는 아니지만, 속은 촉촉하고 겉은 보송한 **세미매트** 제형이라 고객님께 더 잘 맞을 수 있어요!"라고 설득하세요.

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
                temperature=0.7 
            )
            
            assistant_message = response.choices[0].message.content
            
            return {
                "assistant_message": assistant_message,
                "recommendations": candidate_products[:3], 
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