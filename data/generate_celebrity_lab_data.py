import csv
import cv2
import numpy as np
import os
import sys
import re
from pathlib import Path

CELEBRITIES = ["jennie", "karina", "wonyoung"]
DATA_BASE_DIR = "/home/jeongmin/GENAI_project/data"
OUTPUT_BASE_DIR = "/home/jeongmin/GENAI_project/data/product"

def lab_to_rgb(L, a, b):
    lab_pixel = np.uint8([[[L, a, b]]])
    bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)[0][0]
    rgb = (int(bgr_pixel[2]), int(bgr_pixel[1]), int(bgr_pixel[0]))
    return rgb

def lab_to_hex(L, a, b):
    r, g, b_val = lab_to_rgb(L, a, b)
    return f"#{r:02x}{g:02x}{b_val:02x}"

def get_color_description(L, a, b):
    if L < 70:
        brightness = "어두운"
    elif L < 120:
        brightness = "중간"
    elif L < 180:
        brightness = "밝은"
    else:
        brightness = "매우 밝은"
    
    if abs(a - 128) < 15 and abs(b - 128) < 15:
        return f"{brightness} 무채색"
    
    hue_desc = []
    if a > 155:
        hue_desc.append("빨강")
    elif a < 100:
        hue_desc.append("초록")
    
    if b > 155:
        hue_desc.append("노랑")
    elif b < 100:
        hue_desc.append("파랑")
    
    if len(hue_desc) == 0:
        return f"{brightness} 중성"
    
    return f"{brightness} {'+'.join(hue_desc)}"

def extract_lab_from_log(log_path):
    if not os.path.exists(log_path):
        print(f"로그 파일이 없습니다: {log_path}")
        return []
    
    lab_data = []
    current_image = None
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if '처리 중:' in line:
                match = re.search(r'처리 중: (.+\.(jpg|png|jpeg|JPG|PNG|JPEG))', line)
                if match:
                    current_image = match.group(1)
            
            elif 'LAB 값:' in line:
                continue
            
            elif current_image and ('lips' in line or 'cheeks' in line or 'eyeshadow' in line):
                for region in ['lips', 'cheeks', 'eyeshadow']:
                    if region in line:
                        match = re.search(r'\(([\d.]+),\s*([\d.]+),\s*([\d.]+)\)', line)
                        if match:
                            L, a, b = float(match.group(1)), float(match.group(2)), float(match.group(3))
                            lab_data.append({
                                'image': current_image,
                                'region': region,
                                'L': L,
                                'a': a,
                                'b': b
                            })
                        break
    
    return lab_data

def scan_roi_folders(celebrity_name):
    data_dir = Path(DATA_BASE_DIR) / celebrity_name
    
    if not data_dir.exists():
        print(f"데이터 폴더가 없습니다: {data_dir}")
        return []
    
    lab_data = []
    
    roi_files = sorted([f for f in data_dir.glob("*_roi_*.png")])
    
    image_numbers = set()
    for roi_file in roi_files:
        match = re.match(r'(\d+)_roi_(\w+)\.png', roi_file.name)
        if match:
            image_numbers.add(int(match.group(1)))
    
    for img_num in sorted(image_numbers):
        for region in ['lips', 'cheeks', 'eyeshadow']:
            roi_path = data_dir / f"{img_num}_roi_{region}.png"
            
            if roi_path.exists():
                img = cv2.imread(str(roi_path))
                if img is not None:
                    mask = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
                    
                    if mask.sum() > 0:
                        lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                        mean_lab = cv2.mean(lab_img, mask=mask)[:3]
                        
                        lab_data.append({
                            'image': f"{img_num}.jpg",
                            'region': region,
                            'L': mean_lab[0],
                            'a': mean_lab[1],
                            'b': mean_lab[2]
                        })
    
    return lab_data

def save_to_csv(lab_data, output_path, celebrity_name):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Image', 'Region', 'L', 'a', 'b', 'RGB_R', 'RGB_G', 'RGB_B', 'HEX', 'Description'])
        
        for data in lab_data:
            L, a, b = data['L'], data['a'], data['b']
            rgb = lab_to_rgb(L, a, b)
            hex_code = lab_to_hex(L, a, b)
            desc = get_color_description(L, a, b)
            
            writer.writerow([
                data['image'], data['region'],
                f"{L:.2f}", f"{a:.2f}", f"{b:.2f}",
                rgb[0], rgb[1], rgb[2],
                hex_code, desc
            ])
    
    print(f"  CSV 저장 완료: {output_path}")

def generate_html(lab_data, output_path, celebrity_name):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{celebrity_name.upper()} 메이크업 ROI 색상 분석</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            padding: 20px; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            margin: 0;
        }}
        h1 {{ 
            text-align: center; 
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2em;
        }}
        .subtitle {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}
        .image-section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .image-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .regions {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        .region-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .region-card.lips {{ border-left-color: #e74c3c; }}
        .region-card.cheeks {{ border-left-color: #f39c12; }}
        .region-card.eyeshadow {{ border-left-color: #9b59b6; }}
        .region-name {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
            text-transform: uppercase;
        }}
        .color-swatch {{
            width: 100%;
            height: 80px;
            border-radius: 6px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            border: 1px solid #ddd;
        }}
        .color-info {{
            font-size: 0.85em;
            color: #555;
            margin: 5px 0;
            font-family: 'Courier New', monospace;
        }}
        .color-desc {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 8px;
            font-style: italic;
        }}
        .legend {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>{celebrity_name.upper()} 메이크업 ROI 색상 분석</h1>
    <div class="subtitle">MediaPipe 얼굴 파싱을 통한 립, 치크, 아이섀도우 영역 LAB 색상 추출</div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background-color: #e74c3c;"></div>
            <span>립 (Lips)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #f39c12;"></div>
            <span>치크 (Cheeks)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #9b59b6;"></div>
            <span>아이섀도우 (Eyeshadow)</span>
        </div>
    </div>
"""
    
    image_data = {}
    for data in lab_data:
        img_name = data['image']
        if img_name not in image_data:
            image_data[img_name] = {}
        
        image_data[img_name][data['region']] = {
            'L': data['L'],
            'a': data['a'],
            'b': data['b'],
            'rgb': lab_to_rgb(data['L'], data['a'], data['b']),
            'hex': lab_to_hex(data['L'], data['a'], data['b']),
            'desc': get_color_description(data['L'], data['a'], data['b'])
        }
    
    for idx, (filename, regions) in enumerate(sorted(image_data.items()), 1):
        html += f"""
    <div class="image-section">
        <div class="image-title">{idx}. {filename}</div>
        <div class="regions">
"""
        
        region_order = ['lips', 'cheeks', 'eyeshadow']
        region_names = {
            'lips': '립 (Lips)',
            'cheeks': '치크 (Cheeks)',
            'eyeshadow': '아이섀도우 (Eyeshadow)'
        }
        
        for region in region_order:
            if region in regions:
                data = regions[region]
                html += f"""
            <div class="region-card {region}">
                <div class="region-name">{region_names[region]}</div>
                <div class="color-swatch" style="background-color: {data['hex']};"></div>
                <div class="color-info">LAB: L={data['L']:.1f}, a={data['a']:.1f}, b={data['b']:.1f}</div>
                <div class="color-info">RGB: ({data['rgb'][0]}, {data['rgb'][1]}, {data['rgb'][2]})</div>
                <div class="color-info">HEX: {data['hex']}</div>
                <div class="color-desc">{data['desc']}</div>
            </div>
"""
        
        html += """
        </div>
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"  HTML 저장 완료: {output_path}")

def process_celebrity(celebrity_name):
    print(f"\n{'='*70}")
    print(f"{celebrity_name.upper()} 처리 중")
    print(f"{'='*70}")
    
    lab_data = scan_roi_folders(celebrity_name)
    
    if not lab_data:
        print(f"  LAB 데이터를 찾을 수 없습니다.")
        return
    
    print(f"  총 {len(lab_data)}개 영역 데이터 발견")
    
    output_dir = Path(OUTPUT_BASE_DIR)
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = output_dir / f"{celebrity_name}_lab_colors.csv"
    html_path = output_dir / f"{celebrity_name}_lab_colors.html"
    
    save_to_csv(lab_data, str(csv_path), celebrity_name)
    generate_html(lab_data, str(html_path), celebrity_name)
    
    print(f"  완료!")

def main():
    print("="*70)
    print("셀럽 LAB 색상 데이터 CSV/HTML 생성")
    print("="*70)
    
    for celebrity in CELEBRITIES:
        process_celebrity(celebrity)
    
    print("\n" + "="*70)
    print("전체 처리 완료!")
    print(f"출력 디렉토리: {OUTPUT_BASE_DIR}")
    print("="*70)

if __name__ == "__main__":
    main()
