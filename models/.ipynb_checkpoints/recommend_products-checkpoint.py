import sys
import os
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from face_parser import MPFaceParser

# --------------------------------------------------
# 경로 설정
# --------------------------------------------------
PRODUCT_DIR = "/home/jeongmin/genai/data/product"
LIP_CSV   = os.path.join(PRODUCT_DIR, "lip.csv")
CHEEK_CSV = os.path.join(PRODUCT_DIR, "cheek.csv")
EYE_CSV   = os.path.join(PRODUCT_DIR, "eye.csv")


# --------------------------------------------------
# 색상 유틸: OpenCV Lab -> 표준 Lab, Hue/Chroma, ΔE
# --------------------------------------------------
def opencv_lab_to_standard(L_cv: float, a_cv: float, b_cv: float):
    """OpenCV LAB (L:0~255, a/b:0~255) -> CIE Lab 표준 범위 (L:0~100, a/b:-128~127)"""
    L_std = L_cv * 100.0 / 255.0
    a_std = a_cv - 128.0
    b_std = b_cv - 128.0
    return L_std, a_std, b_std


def compute_hue_chroma(a_std: float, b_std: float):
    """표준 Lab의 a/b에서 hue(각도)와 chroma(채도) 계산"""
    hue = np.degrees(np.arctan2(b_std, a_std)) % 360.0
    chroma = float(np.sqrt(a_std * a_std + b_std * b_std))
    return hue, chroma


def deltaE_simple(l1, a1, b1, l2, a2, b2):
    """CIE76 방식의 단순 ΔE. 표준 Lab 좌표에서 사용."""
    return float(np.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2))


# --------------------------------------------------
# Hue + a/b 비율 기반 톤 그룹핑
#  - 여기서 사람이 느끼는 '코랄/핑크/모브/브라운'을 강제로 분리
# --------------------------------------------------
def classify_tone_group(hue: float, a_std: float, b_std: float):
    """
    아주 러프한 규칙:
    - 코랄/웜핑크:  10~70°, b_std > 5, a/b 비율 1.0~3.5
    - 쿨핑크:      330~360 or 0~20°, b_std >= -5, a_std > 10
    - 모브/퍼플:   280~330°, b_std < 0, a_std > 5
    - 브라운/오렌지: 40~80°, b_std > 10, a_std < 35
    - 뉴트럴/MLBB: a_std, b_std 모두 작은 영역
    """

    # 코랄/웜핑크
    if 10 <= hue <= 70 and b_std > 5:
        ratio = abs(a_std) / max(abs(b_std), 1e-3)
        if 1.0 <= ratio <= 3.5:
            return "coral_warm"

    # 쿨핑크 (퍼플 쪽보단 핑크 쪽)
    if (hue >= 330 or hue <= 20) and b_std >= -5 and a_std > 10:
        return "pink_cool"

    # 모브/퍼플
    if 280 <= hue <= 330 and b_std < 0 and a_std > 5:
        return "mauve_purple"

    # 브라운/오렌지
    if 40 <= hue <= 80 and b_std > 10 and a_std < 35:
        return "brown_orange"

    # 뉴트럴/MLBB 비슷한 느낌
    if abs(a_std) < 12 and abs(b_std) < 12:
        return "neutral_mlbb"

    # 나머지는 기타
    return "other"


# --------------------------------------------------
# CSV → 표준 Lab / hue / chroma / tone_group 추가
# --------------------------------------------------
def load_and_annotate_products(csv_path: str, is_standard_lab: bool = False):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    required_cols = {"lab_L", "lab_a", "lab_b"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"{csv_path} 에 lab_L/lab_a/lab_b 컬럼이 없습니다.")

    df = df.dropna(subset=["lab_L", "lab_a", "lab_b"]).copy()

    L_std_list = []
    a_std_list = []
    b_std_list = []
    hue_list = []
    chroma_list = []
    tone_group_list = []

    for _, row in df.iterrows():
        L_val = float(row["lab_L"])
        a_val = float(row["lab_a"])
        b_val = float(row["lab_b"])

        if is_standard_lab:
            L_std, a_std, b_std = L_val, a_val, b_val
        else:
            L_std, a_std, b_std = opencv_lab_to_standard(L_val, a_val, b_val)
            
        h, c = compute_hue_chroma(a_std, b_std)
        tg = classify_tone_group(h, a_std, b_std)

        L_std_list.append(L_std)
        a_std_list.append(a_std)
        b_std_list.append(b_std)
        hue_list.append(h)
        chroma_list.append(c)
        tone_group_list.append(tg)

    df["L_std"] = L_std_list
    df["a_std"] = a_std_list
    df["b_std"] = b_std_list
    df["hue"] = hue_list
    df["chroma"] = chroma_list
    df["tone_group"] = tone_group_list

    return df


# --------------------------------------------------
# 얼굴에서 영역별 LAB 추출 (Face Parser 사용)
# --------------------------------------------------
def extract_face_labs(image_path: str):
    """
    MPFaceParser로 lips / cheeks / eyeshadow 마스크를 얻고,
    각 마스크에서 OpenCV LAB 평균값을 구함.
    
    립의 경우: 채도와 밝기가 높은 상위 20% 픽셀만 사용하여
    그림자/어두운 부분을 제외하고 실제 립스틱 색상만 추출
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"이미지를 불러올 수 없습니다: {image_path}")

    parser = MPFaceParser()
    regions = parser.parse(img_bgr)

    lab_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    hsv_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    def mean_lab_for_mask(mask: np.ndarray, region_type: str = "default"):
        ys, xs = np.where(mask > 0)
        
        if len(ys) == 0:
            return None
        
        if region_type == "lips":
            lab_pixels = lab_img[ys, xs, :]
            hsv_pixels = hsv_img[ys, xs, :]
            
            S_values = hsv_pixels[:, 1]
            V_values = hsv_pixels[:, 2]
            
            sat_threshold = np.percentile(S_values, 80)
            val_threshold = np.percentile(V_values, 60)
            
            valid_mask = (S_values >= sat_threshold) & (V_values >= val_threshold)
            
            if valid_mask.sum() < 10:
                sat_threshold = np.percentile(S_values, 70)
                val_threshold = np.percentile(V_values, 50)
                valid_mask = (S_values >= sat_threshold) & (V_values >= val_threshold)
            
            if valid_mask.sum() < 5:
                valid_mask = np.ones(len(S_values), dtype=bool)
            
            filtered_pixels = lab_pixels[valid_mask]
            mean = filtered_pixels.mean(axis=0)
            
        elif region_type == "cheeks":
            lab_pixels = lab_img[ys, xs, :]
            hsv_pixels = hsv_img[ys, xs, :]
            
            S_values = hsv_pixels[:, 1]
            V_values = hsv_pixels[:, 2]
            H_values = hsv_pixels[:, 0]
            
            sat_threshold = np.percentile(S_values, 80)
            val_min = np.percentile(V_values, 55)
            val_max = np.percentile(V_values, 98)
            
            valid_mask = (S_values >= sat_threshold) & (V_values >= val_min) & (V_values <= val_max)
            
            if valid_mask.sum() < 50:
                sat_threshold = np.percentile(S_values, 65)
                valid_mask = (S_values >= sat_threshold) & (V_values >= val_min)
                
            if valid_mask.sum() < 20:
                sat_threshold = np.percentile(S_values, 55)
                valid_mask = S_values >= sat_threshold
            
            if valid_mask.sum() < 10:
                valid_mask = np.ones(len(S_values), dtype=bool)
            
            filtered_pixels = lab_pixels[valid_mask]
            mean = filtered_pixels.mean(axis=0)
            
            L_mean, a_mean, b_mean = mean[0], mean[1], mean[2]
            
            L_boost = 20.0
            a_boost = 15.0
            b_reduce = 12.0
            
            L_corrected = min(L_mean + L_boost, 255.0)
            a_corrected = min(a_mean + a_boost, 255.0)
            b_corrected = max(b_mean - b_reduce, 0.0)
            
            mean = np.array([L_corrected, a_corrected, b_corrected])
            
        else:
            region_pixels = lab_img[ys, xs, :]
            mean = region_pixels.mean(axis=0)
        
        return float(mean[0]), float(mean[1]), float(mean[2])

    lips_lab_cv = mean_lab_for_mask(regions["lips"], region_type="lips")
    cheeks_lab_cv = mean_lab_for_mask(regions["cheeks"], region_type="cheeks")
    eyes_lab_cv = mean_lab_for_mask(regions["eyeshadow"])

    return {
        "lips": lips_lab_cv,
        "cheeks": cheeks_lab_cv,
        "eyeshadow": eyes_lab_cv,
    }


# --------------------------------------------------
# tone_group 기반 Top3 추천
# --------------------------------------------------
def generate_reason_with_llm(top3_df, category_kr="립"):
    try:
        from groq import Groq
        
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=GROQ_API_KEY)
        
        prompt = f"""You are a professional K-beauty makeup color analysis expert.

Below are the Top 3 recommended {category_kr} products based on color analysis.
Write a brief explanation for each product in polite Korean (존댓말).

"""
        
        for rank, (_, row) in enumerate(top3_df.iterrows(), start=1):
            prompt += f"""
{rank}위: {row['brand']} - {row['shade_name']}
색상 유사도(ΔE): {row['deltaE']:.2f}
"""
        
        prompt += f"""
CRITICAL RULES - You MUST follow these rules:
1. Write ONLY the product explanations. NO greetings, NO introductions.
2. Start directly with "1위:" without any prefix text.
3. Each product: 2-3 sentences explaining color tone, saturation, brightness.
4. Use natural Korean expressions: MLBB, 로지, 웜톤, 쿨톤, 데일리.
5. NO questions - only make polite declarative statements.
6. NO markdown, NO special characters, NO asterisks, NO bold text.
7. MUST use polite Korean endings: ~습니다, ~해요, ~됩니다 (NOT ~한다, ~이다).
8. Write in a professional, polite tone that customers will appreciate.

Example format:
1위: [브랜드] - [쉐이드명]
이 제품은 [색상 특성] 톤으로 [설명]합니다. [추가 설명]해요.

2위: [브랜드] - [쉐이드명]
...

3위: [브랜드] - [쉐이드명]
...

REMEMBER: Use polite Korean (존댓말) throughout. End sentences with ~습니다, ~해요, ~됩니다.
Write ONLY the explanations, starting with "1위:" immediately.
"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a professional beauty color analyst. Write direct, polite (존댓말) explanations in Korean without any greetings or questions. Use ~습니다, ~해요, ~됩니다 endings. Start immediately with product explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        reason = response.choices[0].message.content
        
        reason = reason.replace('**', '').replace('*', '').replace('###', '').replace('##', '').replace('#', '')
        reason = reason.replace('"""', '').replace("'''", '').replace('```', '')
        
        unwanted_starts = [
            "안녕하세요",
            "K-뷰티",
            "전문적인",
            "AI",
            "컬러 분석",
            "추천된",
            "아래는",
            "다음은"
        ]
        
        lines = reason.split('\n')
        clean_lines = []
        skip_mode = True
        
        for line in lines:
            line = line.strip()
            if not line:
                if not skip_mode:
                    clean_lines.append(line)
                continue
            
            if any(line.startswith(f"{i}위:") for i in [1, 2, 3]):
                skip_mode = False
                clean_lines.append(line)
            elif not skip_mode:
                if not any(unwanted in line for unwanted in ["추천받은 이유가 뭘까요", "이유는 뭘까요", "느낌을给하며"]):
                    clean_lines.append(line)
        
        reason = '\n'.join(clean_lines).strip()
        
        return reason
        
    except Exception as e:
        return f"추천 이유 생성 중 오류 발생: {str(e)}"


def recommend_by_tone(user_lab_cv, df_products, top_k: int = 3, label: str = "립"):
    if user_lab_cv is None:
        return None, None

    L_cv, a_cv, b_cv = user_lab_cv
    L_std, a_std, b_std = opencv_lab_to_standard(L_cv, a_cv, b_cv)
    hue, chroma = compute_hue_chroma(a_std, b_std)
    user_tone_group = classify_tone_group(hue, a_std, b_std)

    if label == "치크":
        group_df = df_products.copy()
    else:
        group_df = df_products[df_products["tone_group"] == user_tone_group].copy()

        if len(group_df) < top_k:
            if user_tone_group == "coral_warm":
                extra = df_products[df_products["tone_group"].isin(["pink_cool", "neutral_mlbb"])].copy()
            elif user_tone_group == "pink_cool":
                extra = df_products[df_products["tone_group"].isin(["coral_warm", "neutral_mlbb"])].copy()
            else:
                extra = df_products.copy()
            group_df = pd.concat([group_df, extra]).drop_duplicates()

    dE_list = []
    for _, row in group_df.iterrows():
        dE = deltaE_simple(
            L_std,
            a_std,
            b_std,
            row["L_std"],
            row["a_std"],
            row["b_std"],
        )
        dE_list.append(dE)
    group_df["deltaE"] = dE_list

    group_df = group_df.sort_values("deltaE").head(top_k)

    return group_df[["brand", "product_name", "shade_name", "deltaE"]], {
        "user_L_std": L_std,
        "user_a_std": a_std,
        "user_b_std": b_std,
        "user_hue": hue,
        "user_chroma": chroma,
        "user_tone_group": user_tone_group,
    }


# --------------------------------------------------
# 메인
# --------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("사용법: python recommend_products.py <이미지 경로>")
        sys.exit(1)

    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"이미지 파일이 존재하지 않습니다: {image_path}")
        sys.exit(1)

    print("=" * 70)
    print("얼굴 이미지 기반 메이크업 제품 추천 (색조 그룹 + ΔE 기반)")
    print("=" * 70)
    print(f"입력 이미지: {image_path}")
    print()

    # 1) 얼굴에서 영역별 Lab 추출
    face_labs = extract_face_labs(image_path)

    print("[1] 얼굴 영역별 색상 (OpenCV Lab → 표준 Lab + Hue/Chroma)")
    for key, lab in face_labs.items():
        if lab is None:
            print(f"  {key}: 인식 실패")
        else:
            L_cv, a_cv, b_cv = lab
            L_std, a_std, b_std = opencv_lab_to_standard(L_cv, a_cv, b_cv)
            h, c = compute_hue_chroma(a_std, b_std)
            tg = classify_tone_group(h, a_std, b_std)
            print(
                f"  {key}: "
                f"OpenCV Lab=({L_cv:.1f}, {a_cv:.1f}, {b_cv:.1f}), "
                f"Std Lab=({L_std:.1f}, {a_std:.1f}, {b_std:.1f}), "
                f"Hue={h:.1f}°, Chroma={c:.1f}, ToneGroup={tg}"
            )
    print()

    # 2) CSV 로드 + 색조 그룹 주석
    print("[2] 제품 CSV 로드 및 색조 그룹 주석")
    lip_df   = load_and_annotate_products(LIP_CSV, is_standard_lab=False)
    cheek_df = load_and_annotate_products(CHEEK_CSV, is_standard_lab=True)
    eye_df   = load_and_annotate_products(EYE_CSV, is_standard_lab=False)
    print("  - lip / cheek / eye 각각 tone_group 할당 완료")
    print()

    # 3) tone_group 기반 Top3 추천
    print("[3] Tone Group 기반 Top3 추천 결과")
    print("-" * 60)

    # 립
    lip_reco, lip_info = recommend_by_tone(face_labs["lips"], lip_df, top_k=3, label="립")
    print("립 Top3:")
    if lip_reco is None or len(lip_reco) == 0:
        print("  추천 불가 (립 영역 인식 실패)")
    else:
        print(
            f"  사용자 립: Hue={lip_info['user_hue']:.1f}°, "
            f"Chroma={lip_info['user_chroma']:.1f}, "
            f"ToneGroup={lip_info['user_tone_group']}"
        )
        for i, row in enumerate(lip_reco.itertuples(index=False), start=1):
            print(
                f"  {i}위: {row.brand} - {row.product_name} {row.shade_name} "
                f"(ΔE={row.deltaE:.2f})"
            )
        
        print("\n  [추천 이유]")
        lip_reason = generate_reason_with_llm(lip_reco, category_kr="립")
        print(f"  {lip_reason}")
    print()

    # 치크
    cheek_reco, cheek_info = recommend_by_tone(face_labs["cheeks"], cheek_df, top_k=3, label="치크")
    print("치크 Top3:")
    if cheek_reco is None or len(cheek_reco) == 0:
        print("  추천 불가 (치크 영역 인식 실패)")
    else:
        print(
            f"  사용자 치크: Hue={cheek_info['user_hue']:.1f}°, "
            f"Chroma={cheek_info['user_chroma']:.1f}, "
            f"ToneGroup={cheek_info['user_tone_group']}"
        )
        for i, row in enumerate(cheek_reco.itertuples(index=False), start=1):
            print(
                f"  {i}위: {row.brand} - {row.product_name} {row.shade_name} "
                f"(ΔE={row.deltaE:.2f})"
            )
        
        print("\n  [추천 이유]")
        cheek_reason = generate_reason_with_llm(cheek_reco, category_kr="치크")
        print(f"  {cheek_reason}")
    print()

    # 아이섀도우
    eye_reco, eye_info = recommend_by_tone(face_labs["eyeshadow"], eye_df, top_k=3, label="아이섀도우")
    print("아이섀도우 Top3:")
    if eye_reco is None or len(eye_reco) == 0:
        print("  추천 불가 (아이섀도우 영역 인식 실패)")
    else:
        print(
            f"  사용자 아이: Hue={eye_info['user_hue']:.1f}°, "
            f"Chroma={eye_info['user_chroma']:.1f}, "
            f"ToneGroup={eye_info['user_tone_group']}"
        )
        for i, row in enumerate(eye_reco.itertuples(index=False), start=1):
            print(
                f"  {i}위: {row.brand} - {row.product_name} {row.shade_name} "
                f"(ΔE={row.deltaE:.2f})"
            )
        
        print("\n  [추천 이유]")
        eye_reason = generate_reason_with_llm(eye_reco, category_kr="아이섀도우")
        print(f"  {eye_reason}")
    print()


if __name__ == "__main__":
    main()