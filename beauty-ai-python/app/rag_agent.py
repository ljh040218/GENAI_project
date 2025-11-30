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

def normalize_category(value: str) -> str:
    if not value:
        return "unknown"

    value = value.lower()

    mapping = {
        "lips": ["lip", "lips", "립", "립스틱", "틴트", "립밤", "글로스"],
        "cheeks": ["cheek", "cheeks", "치크", "블러셔", "볼"],
        "eyes": ["eye", "eyes", "아이", "섀도우", "팔레트", "눈"]
    }

    for k, aliases in mapping.items():
        if value in aliases:
            return k

    return "unknown"
    
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
            
            # category가 'unknown'인 경우 WHERE 절에서 제외하여 검색 범위 넓힘 (선택적)
            # 현재는 정확성을 위해 WHERE category = %s 유지
            if category == "unknown":
                 logger.warning("Category is 'unknown'. Searching without category filter.")
                 # 카테고리 필터 없이 검색하는 경우:
                 cur.execute("""
                    SELECT brand, product_name, color_name, price, text, metadata,
                           embedding <=> %s::vector as distance
                    FROM product_embeddings
                    ORDER BY distance ASC
                    LIMIT %s
                 """, (query_embedding, top_k))
            else:
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
                    # NULL 값(NoneType)이 .lower()에서 오류를 일으키지 않도록 안전하게 변환
                    "brand": str(row[0]) if row[0] is not None else "",
                    "product_name": str(row[1]) if row[1] is not None else "",
                    "shade_name": str(row[2]) if row[2] is not None else "",
                    "price": row[3],
                    "rag_text": str(row[4]) if row[4] is not None else "", 
                    "metadata": meta,
                    "distance": float(row[6]),
                    "finish": meta.get("texture", "unknown") 
                })
            
            cur.close()
            conn.close()
            logger.info(f"🔍 [DB Search] Found {len(results)} products for query: '{query_text}' in category: '{category}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []

class IntentClassifier:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def classify(self, user_message: str) -> str:
        prompt = f"""
        사용자 메시지: "{user_message}"
        
        위 메시지의 의도를 다음 중 하나로 분류해:
        - "trend": 최신 뷰티 트렌드, 유행 정보, 시즌별 트렌드 질문
        - "explain": MLBB, 쿨톤/웜톤, 채도, 톤 크로스 등 색조 이론/개념 설명 요청
        - "recommend": 제품 추천 또는 재추천 요청 (기본값)
        
        JSON 형식으로 출력:
        {{
          "intent": "trend / explain / recommend 중 하나"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You must output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )

            raw = response.choices[0].message.content.strip()

            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            try:
                data = json.loads(raw)
                intent = data.get("intent", "recommend")
            except:
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1:
                    try:
                        data = json.loads(raw[start:end+1])
                        intent = data.get("intent", "recommend")
                    except:
                        intent = "recommend"
                else:
                    intent = "recommend"

            if intent not in ["trend", "explain", "recommend"]:
                intent = "recommend"

            return intent

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
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
          "category": "lips / cheeks / eyes / unknown 중 하나",
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
            "category": normalize_category(data.get("category")),
            "brightness": data.get("brightness", "unknown"),
            "saturation": data.get("saturation", "unknown"),
            "like_keywords": data.get("like_keywords", []),
            "dislike_keywords": data.get("dislike_keywords", []),
        }

class RAGAgent:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.intent_classifier = IntentClassifier()
        
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.feedback_parser = FeedbackParser(api_key=api_key)

    def perform_web_search(self, query: str) -> str:
        if DDGS is None:
            return "웹 검색 라이브러리(duckduckgo-search)가 설치되지 않아 검색할 수 없습니다."

        try:
            logger.info(f"Web Searching for: {query}")
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            
            if not results:
                return "검색 결과가 없습니다."
            
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
        category: str # <--- 이 인자는 기존 API의 기본값일 수 있음
    ) -> Dict:
        intent = self.intent_classifier.classify(message)
        logger.info(f"🤖 User Intent: {intent}")

        parsed_pref = self.feedback_parser.parse_preference(message)
        logger.info(f"🧠 Parsed User Preference: {parsed_pref}")
        
        # 🌟 핵심 수정: 사용자가 메시지에서 요청한 카테고리를 최우선으로 사용
        search_category = parsed_pref.get("category", "unknown")
        if search_category == "unknown":
            # 메시지에서 카테고리 파악이 안되면, API에 전달된 기본 category 인자 사용 (예: 'lips')
            search_category = category
            
        logger.info(f"🔎 Final Search Category determined: {search_category}")


        feedback_id = str(uuid.uuid4())
        self.vector_db.save_feedback(
            feedback_id=feedback_id,
            user_id=user_id,
            text=message,
            metadata={
                "preferences": parsed_pref,
                # DB 저장 시에는 메시지에서 파악된 카테고리 사용
                "category": parsed_pref.get("category", "unknown"), 
                "intent": intent,
                "timestamp": str(uuid.uuid1())
            }
        )

        similar_feedbacks = self.vector_db.search_similar_feedbacks(message, user_id, top_k=3)

        if intent == "trend":
            search_context = self.perform_web_search(message)
            return self.generate_trend_response(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                search_context=search_context
            )

        if intent == "explain":
            return self.generate_explain_response(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                memories=similar_feedbacks
            )

        like_keywords_str = " ".join(parsed_pref.get('like_keywords', []))
        search_query = f"{message} {like_keywords_str} {like_keywords_str}"

        db_products = self.vector_db.search_products(
            query_text=search_query,
            category=search_category, # 🌟 수정된 카테고리 사용
            top_k=20
        )

        for p in db_products:
            p["score"] = self.score_product(
                product=p,
                parsed_pref=parsed_pref,
                user_profile=user_profile,
            )

        db_products.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        final_candidates = db_products[:5]

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

        return self.generate_recommend_response(
            user_text=message,
            user_profile=user_profile,
            parsed_pref=parsed_pref,
            memories=similar_feedbacks,
            candidate_products=final_candidates
        )

    def score_product(
        self,
        product: Dict,
        parsed_pref: Dict,
        user_profile: Dict
    ) -> float:
        score = 0.0

        user_tone = user_profile.get("tone", "").lower()
        pref_tone = parsed_pref.get("tone", "").lower()
        product_metadata = product.get("metadata", {})
        
        if isinstance(product_metadata, str):
            try:
                product_metadata = json.loads(product_metadata)
            except:
                product_metadata = {}

        product_pc = product_metadata.get("personal_color", "")
        
        # 1. 일반 키워드 점수 (기존 로직 유지)
        # rag_text는 VectorDB.search_products에서 NoneType 오류를 방지하도록 수정됨
        rag_text_lower = product.get("rag_text", "").lower()
        
        for keyword in parsed_pref.get("like_keywords", []):
            if keyword.lower() in rag_text_lower:
                score += 1.5
        
        for keyword in parsed_pref.get("dislike_keywords", []):
            if keyword.lower() in rag_text_lower:
                score -= 2.0

        # 2. 🌟 핵심 수정: 선호 브랜드/명시적 브랜드 언급에 강력한 가산점 부여
        
        # 2-1. 사용자 프로필의 선호 브랜드
        fav_brands = [b.lower() for b in user_profile.get("fav_brands", [])]
        # brand는 VectorDB.search_products에서 NoneType 오류를 방지하도록 수정됨
        product_brand = product.get("brand", "").lower()
        
        if product_brand in fav_brands:
            score += 3.0 # 프로필 선호 브랜드에 높은 가산점
            
        # 2-2. 대화에서 명시적으로 언급된 브랜드 키워드
        # '크리니크 블러셔 추천해줘'처럼 키워드에 브랜드가 포함될 경우
        brand_keywords = ["크리니크", "맥", "샤넬"] # 자주 언급될 수 있는 브랜드 목록 (예시)
        explicit_keywords = parsed_pref.get("like_keywords", [])
        
        for keyword in explicit_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in brand_keywords or keyword_lower == product_brand:
                # 사용자가 명시적으로 요구한 브랜드에 매우 높은 가산점
                score += 5.0 
                break # 하나의 브랜드만 매칭되어도 충분
                
        # 3. 톤 매칭 로직 (필요하다면 추가)
        # 예: user_tone과 product_pc가 일치하면 score += 1.0 (현재는 제외하고 요청 문제만 해결)
        
        return score

    def generate_recommend_response(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        memories: List[Dict],
        candidate_products: List[Dict]
    ) -> Dict:
        top_candidates = candidate_products[:2] if candidate_products else []

        if top_candidates:
            products_context = "\n".join([
                f"""
[제품 {idx+1}]
- 브랜드: {p['brand']}
- 이름: {p['product_name']} ({p['shade_name']})
- 가격: {p['price']}원
- 상세정보/리뷰요약: {p.get('rag_text', '정보 없음')}
""" for idx, p in enumerate(top_candidates)
            ])
        else:
            products_context = "검색된 적합한 제품이 없습니다."

        system_prompt = f"""
당신은 융통성 있고 설득력 있는 K-Beauty AI 뷰티 에이전트입니다.
단순 정보 나열이 아니라, 퍼스널 컬러 전문가처럼 사용자를 설득해야 합니다.

[사용자 프로필]
- 퍼스널 컬러: {user_profile.get('tone', '알 수 없음')}
- 선호 브랜드: {', '.join(user_profile.get('fav_brands', []))}
- 선호 피니시: {', '.join(user_profile.get('finish_preference', []))}

[현재 대화에서 파악된 사용자 의도]
- 원하는 톤: {parsed_pref.get('tone')}
- 원하는 피니시: {parsed_pref.get('finish')}
- 원하는 카테고리 : {parsed_pref.get('category')}
- 선호 키워드: {', '.join(parsed_pref.get('like_keywords', []))}

[후보 제품 목록 (DB 기반)]
{products_context}

[사용자 질문/불만]
"{user_text}"

[답변 형식 규칙 - 반드시 지킬 것]
1) 반드시 한국어(해요체)로 답변합니다.
2) 답변은 하나의 긴 메시지로 작성하되, 다음 3개 단락 구조를 따릅니다.
   - 1단락: 사용자의 요청과 상황을 공감하며 자연스럽게 요약합니다.
   - 2단락: 추천 제품 1번(제품 1개)에 대해,
     - 어떤 점이 사용자의 피드백/취향에 잘 맞는지,
     - 제형, 컬러 톤, 채도, 각질 부각 여부 등 구체적인 장점을 들어 설명합니다.
   - 3단락: 추천 제품 2번(제품 1개)에 대해,
     - 2단락과는 조금 다른 포인트(예: 데일리/행사용, 채도 차이)를 중심으로 설명하고
     - 어떤 상황에서 2번을 더 추천하는지 정리해 줍니다.
3) 후보 리스트에 **없는** 브랜드명이나 제품명은 절대 언급하지 마세요.
4) 추천 제품은 최대 2개까지입니다.
   - 후보가 2개 이상이면, 상위 2개만 골라서 추천합니다.
   - 후보가 1개 뿐이라면, 2단락에서 그 제품만 자연스럽게 추천하고
     3단락에서는 "이 제품 하나만으로도 충분한 이유"나 활용 팁을 설명합니다.
5) '추천 불가'라는 표현은 절대 사용하지 말고,
   항상 후보 중에서 상대적으로 더 나은 선택지를 제안합니다.
6) 제품 설명에는 위 [후보 제품 목록]에 포함된 정보(브랜드/제품명/컬러/요약 정보)를 중심으로만 사용합니다.
7) 문단 사이에는 빈 줄(한 줄 개행)을 넣어 자연스럽게 구분해 주세요.
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
                "recommendations": top_candidates,
                "parsed_preferences": parsed_pref,
                "intent": "recommend"
            }
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                "assistant_message": "죄송합니다. 재추천 답변을 생성하는 중에 문제가 발생했어요.",
                "recommendations": [],
                "parsed_preferences": parsed_pref,
                "intent": "error"
            }

    def generate_explain_response(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        memories: List[Dict]
    ) -> Dict:
        system_prompt = f"""
당신은 한국어에 능숙한 K-Beauty 색조 이론 전문가입니다.
사용자의 질문에 대해 개념을 차근차근 설명해주는 역할입니다.

[사용자 프로필]
- 퍼스널 컬러(있다면): {user_profile.get('tone', '알 수 없음')}

[현재 대화에서 파악된 사용자 의도]
- 원하는 톤: {parsed_pref.get('tone')}
- 원하는 피니시: {parsed_pref.get('finish')}
- 선호 키워드: {', '.join(parsed_pref.get('like_keywords', []))}

[답변 형식 규칙]
1) 반드시 한국어(해요체)로 답변합니다.
2) 제품을 직접 추천하거나, 구체적인 브랜드/제품명을 언급하지 않습니다.
3) 대신, 사용자가 헷갈려하는 개념(예: MLBB, 쿨톤/웜톤, 채도, 톤 크로스 등)을
   - 쉬운 예시,
   - 비교 설명,
   - 실제 메이크업 상황 예시
   를 활용해서 설명해 주세요.
4) 마지막 부분에는 사용자가 실제로 제품을 고를 때 적용할 수 있는
   간단한 체크리스트나 팁(예: "테스트해볼 때 이런 점을 확인해보세요")을 추가해 주세요.
5) 말투는 친절하고 부담스럽지 않게, 뷰티 유튜버가 설명해 주듯이 작성해 주세요.
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
                "recommendations": [],
                "parsed_preferences": parsed_pref,
                "intent": "explain"
            }
        except Exception as e:
            logger.error(f"Explain generation failed: {e}")
            return {
                "assistant_message": "죄송합니다. 설명을 생성하는 중에 문제가 발생했어요.",
                "recommendations": [],
                "parsed_preferences": parsed_pref,
                "intent": "error"
            }

    def generate_trend_response(
        self,
        user_text: str,
        user_profile: Dict,
        parsed_pref: Dict,
        search_context: str
    ) -> Dict:
        system_prompt = f"""
당신은 최신 K-Beauty 트렌드를 설명하는 전문가입니다.

[사용자 프로필]
- 퍼스널 컬러: {user_profile.get('tone', '알 수 없음')}

[웹 검색 결과]
{search_context}

[사용자 질문]
"{user_text}"

[답변 규칙]
1) 반드시 한국어(해요체)로 답변합니다.
2) 웹 검색 결과를 바탕으로 최신 트렌드를 설명합니다.
3) 구체적인 제품명보다는 트렌드 경향(색상, 텍스처, 스타일 등)에 집중합니다.
4) 친근하고 정보성 있는 톤으로 작성합니다.
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
                "recommendations": [],
                "parsed_preferences": parsed_pref,
                "intent": "trend"
            }
        except Exception as e:
            logger.error(f"Trend generation failed: {e}")
            return {
                "assistant_message": "죄송합니다. 트렌드 정보를 생성하는 중에 문제가 발생했어요.",
                "recommendations": [],
                "parsed_preferences": parsed_pref,
                "intent": "error"
            }