from fastapi import FastAPI, UploadFile
from utils.color_utils import rgb_to_lab, deltaE

app = FastAPI()

@app.post("/analyze")
async def analyze(file: UploadFile):
    # TODO: 얼굴 분석 + 색상 추출 + DB 비교
    return {"status": "ok", "message": "AI pipeline placeholder"}