from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import cv2
import numpy as np
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경변수 로드 확인
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_DATABASE_URL = os.getenv("VECTOR_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not VECTOR_DATABASE_URL:
    raise ValueError("VECTOR_DATABASE_URL environment variable is required")

# 모듈 임포트
from .face_matcher import FaceMatcher
from .product_matcher import ProductMatcher
from .rag_agent import VectorDB, RAGAgent

app = FastAPI(
    title="K-Beauty AI Image Analysis API",
    description="얼굴 이미지 분석 및 K-뷰티 제품 추천 API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. 기존 매처 초기화 (유지)
face_matcher = FaceMatcher(
    database_url=DATABASE_URL,
    openai_api_key=OPENAI_API_KEY
)

product_matcher = ProductMatcher(
    database_url=DATABASE_URL,
    openai_api_key=OPENAI_API_KEY
)

# 2. VectorDB 초기화 (인자 제거 -> 환경변수 자동 로드)
vector_db = VectorDB() 

# 3. RAG Agent 초기화 (vector_db만 주입하면 됨)
rag_agent = RAGAgent(vector_db=vector_db)

class ColorInput(BaseModel):
    lab_L: float
    lab_a: float
    lab_b: float
    category: str

class AnalysisResponse(BaseModel):
    success: bool
    lips: Optional[Dict] = None
    cheeks: Optional[Dict] = None
    eyeshadow: Optional[Dict] = None

class AgentRequest(BaseModel):
    user_id: str
    message: str
    current_recommendations: List[Dict]
    user_profile: Dict
    category: str

class FeedbackQuery(BaseModel):
    user_id: str
    query: str
    top_k: int = 5


@app.get("/")
async def root():
    return {
        "message": "K-Beauty AI Image Analysis API",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "intent_classification": "recommend/explain/trend/both",
            "dual_recommendations": "text_based + profile_based",
            "rag_memory": "pgvector embeddings"
        },
        "endpoints": {
            "health": "/health",
            "analyze_image": "/api/analyze/image",
            "analyze_color": "/api/analyze/color",
            "product_recommend": "/api/product/recommend",
            "agent_message": "/api/agent/message",
            "memory_search": "/api/memory/search",
            "memory_stats": "/api/memory/stats/{user_id}",
            "memory_clear": "/api/memory/clear/{user_id}"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "success": True,
        "message": "Python API is running",
        "services": {
            "face_parser": "ready",
            "face_matcher": "ready",
            "database": "connected" if DATABASE_URL else "not configured",
            "vector_db": "connected" if VECTOR_DATABASE_URL else "not configured",
            "openai": "ready" if OPENAI_API_KEY else "not configured",
            "intent_classifier": "ready",
            "rag_agent": "ready",
            "memory_api": "ready"
        }
    }


@app.post("/api/agent/message")
async def agent_message(request: AgentRequest):
    try:
        logger.info(f"Agent message from user {request.user_id}: {request.message}")
        logger.info(f"📥 Received user_profile in main.py: {request.user_profile}")
        logger.info(f"📥 Received category in main.py: {request.category}")
        
        result = rag_agent.process_message(
            user_id=request.user_id,
            message=request.message,
            current_recommendations=request.current_recommendations,
            user_profile=request.user_profile,
            category=request.category
        )
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    try:
        logger.info(f"Received image: {file.filename}")
        
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        logger.info("Extracting face colors...")
        face_colors = face_matcher.extract_face_colors(image)
        
        result = {
            "success": True,
            "lips": None,
            "cheeks": None,
            "eyeshadow": None
        }
        
        # 립 분석
        if face_colors["lips"]:
            logger.info("Analyzing lips...")
            lip_recommendations, lip_info = face_matcher.recommend_products(
                face_colors["lips"], 
                "lips", 
                top_k=3
            )
            
            if lip_recommendations:
                lip_reasons = face_matcher.generate_explanation(
                    lip_recommendations, 
                    "lips"
                )
                
                for i, product in enumerate(lip_recommendations):
                    product["reason"] = lip_reasons[i] if i < len(lip_reasons) else "색상 유사도가 높아 추천된 제품입니다."
                
                result["lips"] = {
                    "color": {
                        "lab_opencv": face_colors["lips"],
                        "lab_standard": [
                            lip_info["user_L_std"],
                            lip_info["user_a_std"],
                            lip_info["user_b_std"]
                        ],
                        "hue": lip_info["user_hue"],
                        "chroma": lip_info["user_chroma"],
                        "tone_group": lip_info["user_tone_group"]
                    },
                    "recommendations": lip_recommendations
                }
        
        # 치크 분석
        if face_colors["cheeks"]:
            logger.info("Analyzing cheeks...")
            cheek_recommendations, cheek_info = face_matcher.recommend_products(
                face_colors["cheeks"], 
                "cheeks", 
                top_k=3
            )
            
            if cheek_recommendations:
                cheek_reasons = face_matcher.generate_explanation(
                    cheek_recommendations, 
                    "cheeks"
                )
                
                for i, product in enumerate(cheek_recommendations):
                    product["reason"] = cheek_reasons[i] if i < len(cheek_reasons) else "색상 유사도가 높아 추천된 제품입니다."
                
                result["cheeks"] = {
                    "color": {
                        "lab_opencv": face_colors["cheeks"],
                        "lab_standard": [
                            cheek_info["user_L_std"],
                            cheek_info["user_a_std"],
                            cheek_info["user_b_std"]
                        ],
                        "hue": cheek_info["user_hue"],
                        "chroma": cheek_info["user_chroma"],
                        "tone_group": cheek_info["user_tone_group"]
                    },
                    "recommendations": cheek_recommendations
                }
        
        # 아이섀도우 분석
        if face_colors["eyeshadow"]:
            logger.info("Analyzing eyeshadow...")
            eye_recommendations, eye_info = face_matcher.recommend_products(
                face_colors["eyeshadow"], 
                "eyes", 
                top_k=3
            )
            
            if eye_recommendations:
                eye_reasons = face_matcher.generate_explanation(
                    eye_recommendations, 
                    "eyes"
                )
                
                for i, product in enumerate(eye_recommendations):
                    product["reason"] = eye_reasons[i] if i < len(eye_reasons) else "색상 유사도가 높아 추천된 제품입니다."
                
                result["eyeshadow"] = {
                    "color": {
                        "lab_opencv": face_colors["eyeshadow"],
                        "lab_standard": [
                            eye_info["user_L_std"],
                            eye_info["user_a_std"],
                            eye_info["user_b_std"]
                        ],
                        "hue": eye_info["user_hue"],
                        "chroma": eye_info["user_chroma"],
                        "tone_group": eye_info["user_tone_group"]
                    },
                    "recommendations": eye_recommendations
                }
        
        logger.info("Analysis completed successfully")
        return result
        
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/analyze/color")
async def analyze_color(color: ColorInput):
    try:
        logger.info(f"Analyzing color: LAB({color.lab_L}, {color.lab_a}, {color.lab_b})")
        
        user_lab_cv = (color.lab_L, color.lab_a, color.lab_b)
        
        recommendations, user_info = face_matcher.recommend_products(
            user_lab_cv,
            color.category,
            top_k=3
        )
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No matching products found")
        
        reasons = face_matcher.generate_explanation(recommendations, color.category)
        
        for i, product in enumerate(recommendations):
            product["reason"] = reasons[i] if i < len(reasons) else "색상 유사도가 높아 추천된 제품입니다."
        
        return {
            "success": True,
            "input_color": {
                "lab_opencv": [color.lab_L, color.lab_a, color.lab_b],
                "lab_standard": [
                    user_info["user_L_std"],
                    user_info["user_a_std"],
                    user_info["user_b_std"]
                ],
                "hue": user_info["user_hue"],
                "chroma": user_info["user_chroma"],
                "tone_group": user_info["user_tone_group"]
            },
            "category": color.category,
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in color analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/product/recommend")
async def product_recommend(
    file: UploadFile = File(...), 
    category: str = Query("lips", description="Product category: lips, cheeks, eyes")
):
    try:
        logger.info(f"Product image analysis - Category: {category}")
        
        contents = await file.read()
        
        user_lab, results = product_matcher.recommend(contents, category, top_k=3)
        
        if not results:
            raise HTTPException(status_code=404, detail="No matching products found")
        
        reasons = product_matcher.generate_explanation(results, category)
        
        for i, product in enumerate(results):
            product["reason"] = reasons[i] if i < len(reasons) else "색상 유사도가 높아 추천된 제품입니다."
        
        return {
            "user_lab": user_lab,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in product recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/search", tags=["Memory Management"])
async def search_feedbacks(query: FeedbackQuery):
    try:
        results = vector_db.search_similar_feedbacks(
            query_text=query.query,
            user_id=query.user_id,
            top_k=query.top_k
        )
        
        return {
            "success": True,
            "query": query.query,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Feedback search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/stats/{user_id}", tags=["Memory Management"])
async def get_user_memory_stats(user_id: str):
    try:
        # VectorDB 내장 메서드를 사용하거나 직접 연결
        conn = vector_db.get_vector_connection() # get_connection -> get_vector_connection (rag_agent.py 메서드명 확인)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*) 
            FROM feedback_embeddings 
            WHERE user_id = %s
        """, (user_id,))
        total_count = cur.fetchone()[0]
        
        cur.execute("""
            SELECT text, created_at
            FROM feedback_embeddings 
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (user_id,))
        recent_feedbacks = [
            {"text": row[0], "created_at": row[1].isoformat()}
            for row in cur.fetchall()
        ]
        
        cur.execute("""
            SELECT metadata->>'intent' as intent, COUNT(*) as count
            FROM feedback_embeddings 
            WHERE user_id = %s
            GROUP BY metadata->>'intent'
        """, (user_id,))
        intent_distribution = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "total_feedbacks": total_count,
            "recent_feedbacks": recent_feedbacks,
            "intent_distribution": intent_distribution
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/memory/clear/{user_id}", tags=["Memory Management"])
async def clear_user_memory(user_id: str):
    try:
        conn = vector_db.get_vector_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM feedback_embeddings 
            WHERE user_id = %s
        """, (user_id,))
        
        deleted_count = cur.rowcount
        conn.commit()
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)