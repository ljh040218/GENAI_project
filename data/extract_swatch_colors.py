import csv
import cv2
import numpy as np
import os
import requests
from io import BytesIO
from PIL import Image
from pathlib import Path
import time

BASE_DIR = "/home/jeongmin/genai/data/product"
CATEGORIES = {
    'lip': 'lip.csv',
    'eye': 'eye.csv',
    'cheek': 'cheek.csv'
}

class ColorExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_image(self, url, timeout=10):
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            img_rgb = img.convert('RGB')
            img_array = np.array(img_rgb)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
        except Exception as e:
            print(f"    이미지 다운로드 실패: {e}")
            return None
    
    def extract_center_region(self, image, center_ratio=0.4):
        h, w = image.shape[:2]
        center_h = int(h * center_ratio)
        center_w = int(w * center_ratio)
        
        y1 = (h - center_h) // 2
        y2 = y1 + center_h
        x1 = (w - center_w) // 2
        x2 = x1 + center_w
        
        return image[y1:y2, x1:x2]
    
    def extract_color_spatial_center(self, image):
        center_region = self.extract_center_region(image, center_ratio=0.5)
        
        h, w = center_region.shape[:2]
        kernel_size = max(5, int(0.03 * min(h, w)))
        eroded = cv2.erode(center_region, np.ones((kernel_size, kernel_size), np.uint8), iterations=1)
        
        if eroded.size == 0:
            eroded = center_region
        
        lab = cv2.cvtColor(eroded, cv2.COLOR_BGR2LAB)
        mean_lab = cv2.mean(lab)[:3]
        
        return mean_lab
    
    def extract_color_high_saturation(self, image, top_percent=0.3):
        center_region = self.extract_center_region(image, center_ratio=0.6)
        
        hsv = cv2.cvtColor(center_region, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        
        threshold = np.percentile(sat, (1 - top_percent) * 100)
        mask = (sat >= threshold).astype(np.uint8) * 255
        
        if mask.sum() == 0:
            mask = np.ones_like(sat, dtype=np.uint8) * 255
        
        lab = cv2.cvtColor(center_region, cv2.COLOR_BGR2LAB)
        mean_lab = cv2.mean(lab, mask=mask)[:3]
        
        return mean_lab
    
    def extract_dominant_color_kmeans(self, image, k=3):
        pixels = image.reshape(-1, 3).astype(np.float32)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
        
        counts = np.bincount(labels.flatten())
        dominant_idx = np.argmax(counts)
        dominant_bgr = centers[dominant_idx]
        
        lab = cv2.cvtColor(np.uint8([[dominant_bgr]]), cv2.COLOR_BGR2LAB)[0][0]
        
        return float(lab[0]), float(lab[1]), float(lab[2])
    
    def extract_lab(self, url):
        img = self.download_image(url)
        if img is None:
            return None, None, None
        
        method1 = self.extract_color_spatial_center(img)
        method2 = self.extract_color_high_saturation(img)
        method3 = self.extract_dominant_color_kmeans(img, k=3)
        
        final_L = (method1[0] + method2[0] + method3[0]) / 3
        final_a = (method1[1] + method2[1] + method3[1]) / 3
        final_b = (method1[2] + method2[2] + method3[2]) / 3
        
        return round(final_L, 2), round(final_a, 2), round(final_b, 2)

def lab_to_rgb(L, a, b):
    lab_pixel = np.uint8([[[L, a, b]]])
    bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)[0][0]
    rgb = (int(bgr_pixel[2]), int(bgr_pixel[1]), int(bgr_pixel[0]))
    return rgb

def lab_to_hex(L, a, b):
    r, g, b_val = lab_to_rgb(L, a, b)
    return f"#{r:02x}{g:02x}{b_val:02x}"

def get_color_name(L, a, b):
    if L < 30:
        return "매우 어두운"
    elif L > 80:
        return "매우 밝은"
    
    if abs(a - 128) < 10 and abs(b - 128) < 10:
        return "무채색/베이지"
    
    if a > 148:
        red_component = "빨강"
    elif a < 108:
        red_component = "초록"
    else:
        red_component = ""
    
    if b > 148:
        yellow_component = "노랑"
    elif b < 108:
        yellow_component = "파랑"
    else:
        yellow_component = ""
    
    if red_component and yellow_component:
        if a > 150 and b < 138:
            return "빨강"
        elif a > 138 and b > 150:
            return "오렌지"
        elif abs(a - 128) < 20 and b > 150:
            return "노랑"
        elif a < 108 and b > 138:
            return "연두"
        elif a < 108 and abs(b - 128) < 20:
            return "초록"
        elif a < 108 and b < 108:
            return "청록"
        elif abs(a - 128) < 20 and b < 108:
            return "파랑"
        elif a > 138 and b < 108:
            return "보라"
        else:
            return f"{red_component}+{yellow_component}"
    elif red_component:
        return red_component
    elif yellow_component:
        return yellow_component
    else:
        return "중성"

def process_csv(category, csv_file):
    print(f"\n{'='*70}")
    print(f"{category.upper()} 처리 중")
    print(f"{'='*70}\n")
    
    csv_path = Path(BASE_DIR) / csv_file
    
    if not csv_path.exists():
        print(f"CSV 파일이 없습니다: {csv_path}")
        return
    
    rows = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        has_lab = 'lab_L' in fieldnames
        
        if not has_lab:
            fieldnames = list(fieldnames) + ['lab_L', 'lab_a', 'lab_b']
        
        extractor = ColorExtractor() if not has_lab else None
        
        for idx, row in enumerate(reader, 1):
            if has_lab:
                rows.append(row)
                print(f"[{idx}] {row['brand']} - {row['shade_name']}: LAB 값 이미 존재")
            else:
                print(f"[{idx}] {row['brand']} - {row['shade_name']}")
                
                swatch_url = row.get('swatch_url', '').strip()
                
                if not swatch_url:
                    print(f"    스와치 URL 없음, 건너뜀")
                    row['lab_L'] = ''
                    row['lab_a'] = ''
                    row['lab_b'] = ''
                    rows.append(row)
                    continue
                
                L, a, b = extractor.extract_lab(swatch_url)
                
                if L is not None:
                    row['lab_L'] = str(L)
                    row['lab_a'] = str(a)
                    row['lab_b'] = str(b)
                    print(f"    성공: L={L}, a={a}, b={b}")
                else:
                    row['lab_L'] = ''
                    row['lab_a'] = ''
                    row['lab_b'] = ''
                    print(f"    실패: LAB 추출 불가")
                
                rows.append(row)
                time.sleep(0.5)
    
    output_path = csv_path
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nCSV 업데이트 완료: {output_path}")
    
    return rows, fieldnames

def generate_html(category, rows):
    print(f"\nHTML 생성 중: {category}")
    
    html_path = Path(BASE_DIR) / f"{category}_color_palette.html"
    
    category_names = {
        'lip': '립 제품',
        'eye': '아이섀도우 제품',
        'cheek': '치크 제품'
    }
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{category_names[category]} 색상 팔레트</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
        h1 {{ text-align: center; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
        .card {{ background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .swatch {{ width: 100%; height: 100px; border-radius: 4px; margin-bottom: 10px; }}
        .info {{ font-size: 12px; }}
        .brand {{ font-weight: bold; color: #333; }}
        .shade {{ color: #666; margin: 5px 0; }}
        .lab {{ color: #999; font-family: monospace; font-size: 11px; }}
    </style>
</head>
<body>
    <h1>{category_names[category]} 색상 팔레트</h1>
    <div class="grid">
"""
    
    valid_rows = []
    for row in rows:
        try:
            L_str = row.get('lab_L', '').strip()
            a_str = row.get('lab_a', '').strip()
            b_str = row.get('lab_b', '').strip()
            
            if L_str and a_str and b_str:
                L = float(L_str)
                a = float(a_str)
                b = float(b_str)
                
                hex_code = lab_to_hex(L, a, b)
                color_name = get_color_name(L, a, b)
                
                valid_rows.append({
                    'brand': row['brand'],
                    'product_name': row['product_name'],
                    'shade_name': row['shade_name'],
                    'L': L,
                    'a': a,
                    'b': b,
                    'hex': hex_code,
                    'color_name': color_name
                })
        except (ValueError, KeyError) as e:
            continue
    
    valid_rows.sort(key=lambda x: x['L'], reverse=True)
    
    for item in valid_rows:
        html += f"""
        <div class="card">
            <div class="swatch" style="background-color: {item['hex']};"></div>
            <div class="info">
                <div class="brand">{item['brand']}</div>
                <div class="shade">{item['shade_name']}</div>
                <div class="lab">LAB: {item['L']:.1f}, {item['a']:.1f}, {item['b']:.1f}</div>
                <div class="lab">{item['hex']} · {item['color_name']}</div>
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML 저장 완료: {html_path}")

def main():
    print("="*70)
    print("제품 색상 LAB 추출 및 HTML 생성")
    print("="*70)
    
    for category, csv_file in CATEGORIES.items():
        rows, fieldnames = process_csv(category, csv_file)
        if rows:
            generate_html(category, rows)
    
    print("\n" + "="*70)
    print("전체 처리 완료!")
    print(f"출력 디렉토리: {BASE_DIR}")
    print("="*70)

if __name__ == "__main__":
    main()