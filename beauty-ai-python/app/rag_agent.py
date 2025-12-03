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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_category(value: str) -> str:
    if not value:
        return "unknown"

    value = value.lower().strip()

    mapping = {
        "lips": ["lip", "lips", "립", "립스틱", "틴트", "립밤", "글로스", "립글로스"],
        "cheeks": ["cheek", "cheeks", "치크", "블러셔", "볼", "블러쉬"],
        "eyes": ["eye", "eyes", "아이", "섀도우", "팔레트", "눈", "아이섀도우"]
    }

    for k, aliases in mapping.items():
        if value in aliases:
            return k

    return "unknown"
    
class VectorDB:
    def __init__(self):
        self.vector_db_url = os.getenv("VECTOR_DATABASE_URL")
        self.general_db_url = os.getenv("DATABASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.vector_db_url or not self.general_db_url:
            raise ValueError("데이터베이스 URL(VECTOR_DATABASE_URL, DATABASE_URL)이 설정되지 않았습니다.")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
            
        self.client = OpenAI(api_key=self.api_key)
    
    def get_vector_connection(self):
        return psycopg2.connect(self.vector_db_url)

    def create_embedding(self, text: str) -> List[float]:
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
        try:
            conn = self.get_vector_connection()
            cur = conn.cursor()
            
            query_embedding = self.create_embedding(query_text)
            
            normalized_category = normalize_category(category)
            
            if normalized_category == "unknown":
                cur.execute("""
                    SELECT 
                        id,
                        brand,
                        product_name,
                        color_name,
                        price,
                        text,
                        metadata,
                        embedding <=> %s::vector as distance
                    FROM product_embeddings
                    ORDER BY distance ASC
                    LIMIT %s
                """, (query_embedding, top_k))
            else:
                cur.execute("""
                    SELECT 
                        id,
                        brand,
                        product_name,
                        color_name,
                        price,
                        text,
                        metadata,
                        embedding <=> %s::vector as distance
                    FROM product_embeddings
                    WHERE category = %s
                    ORDER BY distance ASC
                    LIMIT %s
                """, (query_embedding, normalized_category, top_k))
            
            results = []
            for row in cur.fetchall():
                meta = row[6] if row[6] else {}
                
                results.append({
                    "product_id": str(row[0]) if row[0] is not None else "",
                    "brand": str(row[1]) if row[1] is not None else "",
                    "product_name": str(row[2]) if row[2] is not None else "",
                    "shade_name": str(row[3]) if row[3] is not None else "",
                    "price": row[4],
                    "rag_text": str(row[5]) if row[5] is not None else "",
                    "metadata": meta,
                    "distance": float(row[7]),
                    "finish": meta.get("texture", "unknown")
                })
            
            cur.close()
            conn.close()
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

            return intent

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return "recommend"

class RAGAgent:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.intent_classifier = IntentClassifier()

    def parse_user_preferences(self, user_text: str, memories: List[Dict]) -> Dict:
        memory_context = ""
        if memories:
            memory_items = []
            for i, mem in enumerate(memories[:3]):
                memory_items.append(f"[기록 {i+1}] {mem.get('text', '')}")
            memory_context = "\n".join(memory_items)

        system_prompt = f"""
당신은 사용자가 원하는 화장품 특성을 파악하는 전문가입니다.
사용자의 메시지를 분석하여 다음 정보를 추출하세요:

1. 선호하는 톤 (tone): "warm"(웜톤), "cool"(쿨톤), 또는 ""(언급 없음)
   - "쿨톤", "cool", "차가운", "블루베이스" → cool
   - "웜톤", "warm", "따뜻한", "옐로우베이스" → warm
   - 퍼스널컬러와 무관한 "여름", "겨울", "봄", "가을"은 계절이므로 tone에 포함하지 마세요

2. 카테고리 (category): "lips", "cheeks", "eyes", 또는 ""(언급 없음)
   - "립", "립스틱", "틴트", "립밤", "글로스" → lips
   - "치크", "블러셔", "블러쉬", "볼" → cheeks
   - "아이", "섀도우", "팔레트", "눈" → eyes

3. 피니시 (finish): "matte", "glossy", "satin", "shimmer", "glitter" 등 또는 ""(언급 없음)

4. 선호 브랜드 (preferred_brand): 브랜드명 또는 ""

5. 좋아하는 키워드 (like_keywords): ["자연스러운", "화사한", "생기있는", "데일리", "진한" 등] 또는 []

6. 싫어하는 키워드 (dislike_keywords): ["과한", "촌스러운", "부담스러운" 등] 또는 []

[과거 대화 기록]
{memory_context}

[사용자 메시지]
"{user_text}"

반드시 JSON 형식으로만 출력하세요:
{{
  "tone": "",
  "category": "",
  "finish": "",
  "preferred_brand": "",
  "like_keywords": [],
  "dislike_keywords": []
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.2,
                max_tokens=300
            )

            raw = response.choices[0].message.content.strip()

            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            try:
                parsed = json.loads(raw)
            except:
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1:
                    parsed = json.loads(raw[start:end+1])
                else:
                    parsed = {}

            result = {
                "tone": parsed.get("tone", ""),
                "category": normalize_category(parsed.get("category", "")),
                "finish": parsed.get("finish", ""),
                "preferred_brand": parsed.get("preferred_brand", ""),
                "like_keywords": parsed.get("like_keywords", []),
                "dislike_keywords": parsed.get("dislike_keywords", [])
            }

            return result

        except Exception as e:
            logger.error(f"Preference parsing failed: {e}")
            return {
                "tone": "",
                "category": "unknown",
                "finish": "",
                "preferred_brand": "",
                "like_keywords": [],
                "dislike_keywords": []
            }

    def translate_to_english(self, korean_text: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Translate the following Korean beauty-related text to English. Output ONLY the English translation, no explanations."},
                    {"role": "user", "content": korean_text}
                ],
                temperature=0.3,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return korean_text

    def web_search(self, query: str, max_results: int = 3) -> str:
        if not DDGS:
            logger.warning("DuckDuckGo search is not available. Install: pip install duckduckgo-search")
            return ""

        try:
            english_query = self.translate_to_english(query)
            logger.info(f"Translated query: '{query}' → '{english_query}'")
            
            search_query = f"Korean beauty {english_query} 2024 2025"
            logger.info(f"Searching for: {search_query}")
            
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=max_results))
                
                if not results:
                    logger.warning(f"No web search results found for query: {search_query}")
                    return ""
                
                logger.info(f"Web search successful, found {len(results)} results")
                context = ""
                for i, result in enumerate(results):
                    context += f"[결과 {i+1}]\n"
                    context += f"제목: {result.get('title', 'N/A')}\n"
                    context += f"내용: {result.get('body', 'N/A')}\n\n"
                
                return context
        except Exception as e:
            logger.error(f"Web search failed: {type(e).__name__}: {str(e)}")
            return ""

    def detect_category_from_message(self, message: str) -> str:
        message_lower = message.lower()
        
        lips_keywords = ["립", "틴트", "립스틱", "립밤", "글로스", "립글로스"]
        cheeks_keywords = ["치크", "블러셔", "블러쉬", "볼"]
        eyes_keywords = ["아이", "섀도우", "아이섀도우", "팔레트", "눈"]
        
        last_position = -1
        last_category = "unknown"
        
        for keyword in lips_keywords:
            pos = message_lower.rfind(keyword)
            if pos > last_position:
                last_position = pos
                last_category = "lips"
        
        for keyword in cheeks_keywords:
            pos = message_lower.rfind(keyword)
            if pos > last_position:
                last_position = pos
                last_category = "cheeks"
        
        for keyword in eyes_keywords:
            pos = message_lower.rfind(keyword)
            if pos > last_position:
                last_position = pos
                last_category = "eyes"
        
        return last_category

    def process_message(
        self,
        user_id: str,
        message: str,
        current_recommendations: List[Dict],
        user_profile: Dict,
        category: str
    ) -> Dict:
        memories = self.vector_db.search_similar_feedbacks(message, user_id, top_k=3)
        
        memory_category = "unknown"
        if memories and len(memories) > 0:
            latest_memory = memories[0]
            if latest_memory.get("metadata"):
                parsed_prefs = latest_memory["metadata"].get("parsed_preferences", {})
                memory_category = parsed_prefs.get("category", "unknown")
        
        message_detected_category = self.detect_category_from_message(message)
        
        if message_detected_category != "unknown":
            final_category = message_detected_category
        elif memory_category != "unknown":
            final_category = memory_category
        else:
            final_category = normalize_category(category)

        parsed_pref = self.parse_user_preferences(message, memories)
        
        if parsed_pref.get("category") == "unknown" or not parsed_pref.get("category"):
            parsed_pref["category"] = final_category

        intent = self.intent_classifier.classify(message)

        if intent == "trend":
            search_context = self.web_search(message, max_results=3)
            
            result = self.generate_trend_response(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                search_context=search_context
            )
        
        elif intent == "explain":
            result = self.generate_explain_response(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                memories=memories
            )
        
        else:
            search_category = parsed_pref.get("category", "unknown")
            
            vector_products = self.vector_db.search_products(
                query_text=message,
                category=search_category,
                top_k=20
            )

            scored_products = []
            for product in vector_products:
                score = self.calculate_product_score(
                    product=product,
                    user_profile=user_profile,
                    parsed_pref=parsed_pref,
                    message=message
                )
                scored_products.append((score, product))

            scored_products.sort(key=lambda x: x[0], reverse=True)

            candidate_products = [p for _, p in scored_products[:5]]

            result = self.generate_recommend_response(
                user_text=message,
                user_profile=user_profile,
                parsed_pref=parsed_pref,
                memories=memories,
                candidate_products=candidate_products
            )

        feedback_metadata = {
            "intent": result.get("intent", "unknown"),
            "parsed_preferences": parsed_pref,
            "user_profile": user_profile
        }
        
        feedback_id = str(uuid.uuid4())
        self.vector_db.save_feedback(feedback_id, user_id, message, feedback_metadata)

        return result

    def calculate_product_score(
        self,
        product: Dict,
        user_profile: Dict,
        parsed_pref: Dict,
        message: str
    ) -> float:
        score = 0.0

        base_score = 10.0 - min(product.get("distance", 5.0), 5.0) * 2
        score += base_score

        pref_finish = parsed_pref.get("finish", "").lower()
        product_finish = product.get("finish", "").lower()

        if pref_finish and product_finish:
            if pref_finish == product_finish:
                score += 3.0
            else:
                score -= 1.0

        like_kw = [kw.lower() for kw in parsed_pref.get("like_keywords", [])]
        dislike_kw = [kw.lower() for kw in parsed_pref.get("dislike_keywords", [])]

        product_text = (product.get("rag_text", "") + " " + product.get("shade_name", "")).lower()

        for kw in like_kw:
            if kw in product_text:
                score += 1.5

        for kw in dislike_kw:
            if kw in product_text:
                score -= 2.0

        pref_brand = parsed_pref.get("preferred_brand", "").lower()
        product_brand = product.get("brand", "").lower()

        if pref_brand and pref_brand in product_brand:
            score += 5.0

        fav_brands = [b.lower() for b in user_profile.get("fav_brands", [])]
        if product_brand in fav_brands:
            score += 2.5

        message_lower = message.lower()
        brand_keywords = ["클리오", "롬앤", "페리페라", "에뛰드", "미샤", "더샘"]
        for keyword in brand_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in message_lower and keyword_lower in product_brand:
                score += 5.0
                break
        
        user_tone = user_profile.get("tone", "").lower()
        pref_tone = parsed_pref.get("tone", "").lower()
        product_pc = product.get("rag_text", "").lower()
        
        if pref_tone and pref_tone != "unknown":
            final_tone = pref_tone
        elif user_tone and user_tone != "unknown":
            final_tone = user_tone
        else:
            final_tone = ""
        
        if final_tone and product_pc:
            if final_tone == "warm" or final_tone == "웜":
                if "웜" in product_pc or "warm" in product_pc or "봄" in product_pc or "가을" in product_pc:
                    score += 2.0
                elif "쿨" in product_pc or "cool" in product_pc or "여름" in product_pc or "겨울" in product_pc:
                    score -= 3.0
            elif final_tone == "cool" or final_tone == "쿨":
                if "쿨" in product_pc or "cool" in product_pc or "여름" in product_pc or "겨울" in product_pc:
                    score += 2.0
                elif "웜" in product_pc or "warm" in product_pc or "봄" in product_pc or "가을" in product_pc:
                    score -= 3.0
        
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
- 브랜드: {p.get('brand', '')}
- 이름: {p.get('product_name', '')} ({p.get('shade_name', '')})
- 가격: {p.get('price', 0)}원
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
- 선호 브랜드: {', '.join([b for b in user_profile.get('fav_brands', []) if b])}
- 선호 피니시: {', '.join([f for f in user_profile.get('finish_preference', []) if f])}

[현재 대화에서 파악된 사용자 의도]
- 원하는 톤: {parsed_pref.get('tone')}
- 원하는 피니시: {parsed_pref.get('finish')}
- 원하는 카테고리: {parsed_pref.get('category')}
- 선호 키워드: {', '.join(parsed_pref.get('like_keywords', []))}

**톤 추천 우선순위**:
1. 사용자가 대화에서 **명시적으로 톤을 언급한 경우** (예: "쿨톤 립", "웜톤에 맞는") → 해당 톤 우선
2. 톤 언급이 없으면 → 프로필의 퍼스널 컬러({user_profile.get('tone', '알 수 없음')}) 사용
3. "겨울 트렌드", "여름 메이크업" 등은 계절이며 퍼스널컬러가 아님

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
        if search_context and search_context != "":
            web_info = f"""
[웹 검색 결과]
{search_context}

위 검색 결과를 바탕으로 최신 트렌드를 설명합니다.
"""
        else:
            web_info = """
[참고]
웹 검색 결과가 없으므로, 일반적인 K-Beauty 트렌드 지식을 바탕으로 답변합니다.
최신 정보가 아닐 수 있으니 참고용으로만 활용해주세요.
"""

        system_prompt = f"""
당신은 최신 K-Beauty 트렌드를 설명하는 전문가입니다.

[사용자 프로필]
- 퍼스널 컬러: {user_profile.get('tone', '알 수 없음')}

{web_info}

[사용자 질문]
"{user_text}"

[답변 규칙]
1) 반드시 한국어(해요체)로 답변합니다.
2) 웹 검색 결과가 있으면 이를 바탕으로, 없으면 일반적인 K-Beauty 트렌드 지식으로 설명합니다.
3) 구체적인 제품명보다는 트렌드 경향(색상, 텍스처, 스타일 등)에 집중합니다.
4) 친근하고 정보성 있는 톤으로 작성합니다.
5) 웹 검색 결과가 없는 경우, "참고용 정보"라고 짧게 언급하고 일반적인 트렌드를 설명합니다.
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