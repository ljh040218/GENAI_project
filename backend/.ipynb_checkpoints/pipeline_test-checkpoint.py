import os
import sys
import cv2
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from models.face_parser import MPFaceParser
from utils.color_utils import region_mean_lab, deltaE

INPUT_BASE_DIR = "/home/jeongmin/GENAI_project/celebrity_images"
OUTPUT_BASE_DIR = "/home/jeongmin/GENAI_project/data"

CELEBRITIES = ["jennie", "karina", "wonyoung"]

def process_celebrity_folder(celebrity_name, parser):
    input_dir = Path(INPUT_BASE_DIR) / celebrity_name
    output_dir = Path(OUTPUT_BASE_DIR) / celebrity_name
    
    if not input_dir.exists():
        print(f"입력 폴더가 없습니다: {input_dir}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    image_files = sorted([
        f for f in input_dir.iterdir() 
        if f.is_file() and f.suffix in image_extensions
    ])
    
    if not image_files:
        print(f"이미지 파일이 없습니다: {input_dir}")
        return
    
    print(f"\n{'='*70}")
    print(f"{celebrity_name.upper()} 폴더 처리 시작 ({len(image_files)}개 이미지)")
    print(f"{'='*70}\n")
    
    success_count = 0
    fail_count = 0
    
    for idx, img_path in enumerate(image_files, start=1):
        print(f"[{idx}/{len(image_files)}] 처리 중: {img_path.name}")
        
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  이미지 로드 실패, 건너뜀")
            fail_count += 1
            continue
        
        try:
            masks = parser.parse(img)
            
            for region_name, mask in masks.items():
                vis = cv2.bitwise_and(img, img, mask=mask)
                roi_filename = f"{idx}_roi_{region_name}.png"
                mask_filename = f"{idx}_mask_{region_name}.png"
                cv2.imwrite(str(output_dir / roi_filename), vis)
                cv2.imwrite(str(output_dir / mask_filename), mask)
            
            lab = {k: region_mean_lab(img, m, min_sat=5) for k, m in masks.items()}
            
            print(f"  LAB 값:")
            for k, v in lab.items():
                print(f"    {k:9s} -> {tuple(round(x,2) for x in v)}")
            
            print(f"  ΔE: lips-cheeks={round(deltaE(lab['lips'], lab['cheeks']), 2)}, "
                  f"lips-eyeshadow={round(deltaE(lab['lips'], lab['eyeshadow']), 2)}, "
                  f"cheeks-eyeshadow={round(deltaE(lab['cheeks'], lab['eyeshadow']), 2)}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  처리 실패: {e}")
            fail_count += 1
            continue
        
        print()
    
    print(f"{celebrity_name} 처리 완료: 성공 {success_count}개, 실패 {fail_count}개")
    print(f"저장 폴더: {output_dir.absolute()}\n")

def main():
    print("="*70)
    print("셀럽 이미지 ROI 추출 시작")
    print("="*70)
    
    parser = MPFaceParser()
    
    for celebrity in CELEBRITIES:
        process_celebrity_folder(celebrity, parser)
    
    print("="*70)
    print("전체 처리 완료!")
    print("="*70)

if __name__ == "__main__":
    main()