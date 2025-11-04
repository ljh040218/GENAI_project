import os, sys, time, cv2
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from models.face_parser import MPFaceParser
from utils.color_utils import region_mean_lab, deltaE

IMG_PATH = os.environ.get("IMG_PATH", "1.jpg")
ts = time.strftime("%H%M%S")
img = cv2.imread(IMG_PATH)
if img is None:
    raise FileNotFoundError(f"이미지 로드 실패: {IMG_PATH}")

parser = MPFaceParser()
masks = parser.parse(img)

# ROI 시각화 저장
os.makedirs("debug_out", exist_ok=True)
for k, m in masks.items():
    vis = cv2.bitwise_and(img, img, mask=m)
    cv2.imwrite(f"debug_out/roi_{k}_{ts}.png", vis)
    cv2.imwrite(f"debug_out/mask_{k}_{ts}.png", m)

# LAB 평균 + ΔE 테스트
lab = {k: region_mean_lab(img, m, min_sat=5) for k, m in masks.items()}
print("LAB(lips, cheeks, eyeshadow):")
for k, v in lab.items():
    print(f"  {k:9s} -> {tuple(round(x,2) for x in v)}")

print("\nΔE(lips vs cheeks) =", round(deltaE(lab['lips'], lab['cheeks']), 3))
print("ΔE(lips vs eyeshadow) =", round(deltaE(lab['lips'], lab['eyeshadow']), 3))
print("ΔE(cheeks vs eyeshadow) =", round(deltaE(lab['cheeks'], lab['eyeshadow']), 3))

print(f"\n저장 폴더: {os.path.abspath('debug_out')}")
