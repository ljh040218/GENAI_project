import os
import pandas as pd
from pathlib import Path

CSV_DIR = "/home/jeongmin/genai/crawler"

def copy_swatch_to_image_url(csv_path):
    try:
        df = pd.read_csv(csv_path)
        
        if 'swatch_url' not in df.columns:
            print(f"  ⚠ swatch_url 컬럼 없음, 건너뜀")
            return False
        
        if 'image_url' not in df.columns:
            print(f"  ⚠ image_url 컬럼 없음, 건너뜀")
            return False
        
        before_null_count = df['image_url'].isna().sum()
        
        df['image_url'] = df['swatch_url']
        
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        after_null_count = df['image_url'].isna().sum()
        updated_count = before_null_count - after_null_count
        
        print(f"  ✓ 완료: {updated_count}개 행 업데이트 (총 {len(df)}개 행)")
        return True
        
    except Exception as e:
        print(f"  ✗ 실패: {e}")
        return False

def process_all_csv_files():
    csv_dir = Path(CSV_DIR)
    
    if not csv_dir.exists():
        print(f"디렉토리를 찾을 수 없습니다: {CSV_DIR}")
        return
    
    csv_files = sorted(csv_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"CSV 파일을 찾을 수 없습니다: {CSV_DIR}")
        return
    
    print(f"총 {len(csv_files)}개의 CSV 파일 발견\n")
    
    success_count = 0
    fail_count = 0
    
    for csv_file in csv_files:
        print(f"[{success_count + fail_count + 1}/{len(csv_files)}] 처리 중: {csv_file.name}")
        
        if copy_swatch_to_image_url(csv_file):
            success_count += 1
        else:
            fail_count += 1
        
        print()
    
    print("="*70)
    print(f"처리 완료: 성공 {success_count}개, 실패 {fail_count}개")
    print("="*70)

if __name__ == "__main__":
    print("="*70)
    print("CSV 파일 image_url 컬럼 업데이트")
    print("swatch_url → image_url 복사")
    print("="*70)
    print()
    
    process_all_csv_files()
