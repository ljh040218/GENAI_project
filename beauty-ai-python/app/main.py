from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import cv2
import numpy as np
import os
from dotenv import load_dotenv
import logging

from .color_analyzer import ColorAnalyzer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="K-Beauty AI Image Analysis API",
    description="얼굴 이미지 분석 및 K-뷰티 제품 추천 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

color_analyzer = ColorAnalyzer(
    database_url=DATABASE_URL,
    groq_api_key=GROQ_API_KEY
)


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
    message: Optional[str] = None


@app.get("/")
async def root():
    return {
        "message": "K-Beauty AI Image Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze_image": "/api/analyze/image",
            "analyze_color": "/api/analyze/color"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "success": True,
        "message": "Python API is running",
        "services": {
            "face_parser": "ready",
            "color_analyzer": "ready",
            "database": "connected" if DATABASE_URL else "not configured",
            "llm": "ready" if GROQ_API_KEY else "not configured"
        }
    }


@app.post("/api/analyze/image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    얼굴 이미지를 분석하여 립, 치크, 아이섀도우 색상 추출 및 제품 추천
    """
    try:
        logger.info(f"Received image: {file.filename}")
        
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        logger.info("Extracting face colors...")
        face_colors = color_analyzer.extract_face_colors(image)
        
        result = {
            "success": True,
            "lips": None,
            "cheeks": None,
            "eyeshadow": None
        }
        
        # 립 분석
        if face_colors["lips"]:
            logger.info("Analyzing lips...")
            lip_recommendations, lip_info = color_analyzer.recommend_products(
                face_colors["lips"], 
                "lips", 
                top_k=3
            )
            
            if lip_recommendations:
                lip_explanation = color_analyzer.generate_explanation(
                    lip_recommendations, 
                    "lips"
                )
                
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
                    "recommendations": lip_recommendations,
                    "explanation": lip_explanation
                }
        
        # 치크 분석
        if face_colors["cheeks"]:
            logger.info("Analyzing cheeks...")
            cheek_recommendations, cheek_info = color_analyzer.recommend_products(
                face_colors["cheeks"], 
                "cheeks", 
                top_k=3
            )
            
            if cheek_recommendations:
                cheek_explanation = color_analyzer.generate_explanation(
                    cheek_recommendations, 
                    "cheeks"
                )
                
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
                    "recommendations": cheek_recommendations,
                    "explanation": cheek_explanation
                }
        
        # 아이섀도우 분석
        if face_colors["eyeshadow"]:
            logger.info("Analyzing eyeshadow...")
            eye_recommendations, eye_info = color_analyzer.recommend_products(
                face_colors["eyeshadow"], 
                "eyes", 
                top_k=3
            )
            
            if eye_recommendations:
                eye_explanation = color_analyzer.generate_explanation(
                    eye_recommendations, 
                    "eyes"
                )
                
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
                    "recommendations": eye_recommendations,
                    "explanation": eye_explanation
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
    """
    LAB 색상 값으로 직접 제품 추천
    """
    try:
        logger.info(f"Analyzing color: LAB({color.lab_L}, {color.lab_a}, {color.lab_b})")
        
        user_lab_cv = (color.lab_L, color.lab_a, color.lab_b)
        
        recommendations, user_info = color_analyzer.recommend_products(
            user_lab_cv,
            color.category,
            top_k=3
        )
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No matching products found")
        
        explanation = color_analyzer.generate_explanation(recommendations, color.category)
        
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
            "recommendations": recommendations,
            "explanation": explanation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in color analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)