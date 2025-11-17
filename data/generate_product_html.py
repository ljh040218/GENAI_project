import csv
import cv2
import numpy as np
from pathlib import Path

BASE_DIR = "/home/jeongmin/genai/data/product"

def opencv_lab_to_rgb(L, a, b):
    lab_pixel = np.uint8([[[L, a, b]]])
    bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)[0][0]
    rgb = (int(bgr_pixel[2]), int(bgr_pixel[1]), int(bgr_pixel[0]))
    return rgb

def opencv_lab_to_hex(L, a, b):
    r, g, b_val = opencv_lab_to_rgb(L, a, b)
    return f"#{r:02x}{g:02x}{b_val:02x}"

def get_color_name(L, a, b):
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

def load_product_data(csv_file):
    csv_path = Path(BASE_DIR) / csv_file
    
    if not csv_path.exists():
        print(f"CSV 파일이 없습니다: {csv_path}")
        return []
    
    print(f"CSV 로딩 중: {csv_path}\n")
    
    products = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, 1):
            try:
                L_str = row.get('lab_L', '').strip()
                a_str = row.get('lab_a', '').strip()
                b_str = row.get('lab_b', '').strip()
                
                if not L_str or not a_str or not b_str:
                    continue
                
                L = float(L_str)
                a = float(a_str)
                b = float(b_str)
                
                if L < 0 or L > 255 or a < 0 or a > 255 or b < 0 or b > 255:
                    continue
                
                hex_code = opencv_lab_to_hex(L, a, b)
                color_name = get_color_name(L, a, b)
                
                products.append({
                    'brand': row['brand'],
                    'product_name': row['product_name'],
                    'shade_name': row['shade_name'],
                    'price': row.get('price', ''),
                    'finish': row.get('finish', ''),
                    'L': L,
                    'a': a,
                    'b': b,
                    'hex': hex_code,
                    'color_name': color_name
                })
                
            except (ValueError, KeyError) as e:
                continue
    
    print(f"총 {len(products)}개 제품 로드 완료\n")
    return products

def generate_lip_html(products):
    html_path = Path(BASE_DIR) / "lip_color_palette.html"
    
    print(f"립 HTML 생성 중: {html_path}")
    
    products_sorted = sorted(products, key=lambda x: x['L'], reverse=True)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>립 제품 색상 팔레트</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            padding: 20px; 
            background: linear-gradient(135deg, #ffeef8 0%, #ffe5e5 100%);
            margin: 0;
        }
        h1 { 
            text-align: center; 
            color: #d63384;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #6c757d;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .stats {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); 
            gap: 20px; 
        }
        .card { 
            background: white; 
            padding: 15px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .swatch { 
            width: 100%; 
            height: 120px; 
            border-radius: 8px; 
            margin-bottom: 12px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            border: 2px solid #f0f0f0;
        }
        .info { font-size: 13px; }
        .brand { 
            font-weight: bold; 
            color: #d63384;
            font-size: 14px;
            margin-bottom: 5px;
        }
        .product { 
            color: #495057; 
            font-size: 12px;
            margin-bottom: 5px;
        }
        .shade { 
            color: #212529;
            font-weight: 600;
            margin: 8px 0;
            font-size: 13px;
        }
        .price {
            color: #6c757d;
            font-size: 11px;
            margin-bottom: 8px;
        }
        .lab { 
            color: #868e96; 
            font-family: 'Courier New', monospace; 
            font-size: 11px;
            margin: 3px 0;
        }
        .color-name {
            display: inline-block;
            background: #f8f9fa;
            color: #495057;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>🌸 립 제품 색상 팔레트 🌸</h1>
    <div class="subtitle">K-Beauty 립 제품 색상 분석 (LAB 색공간 기준)</div>
    
    <div class="stats">
        <strong>총 제품 수:</strong> """ + str(len(products_sorted)) + """ 개
    </div>
    
    <div class="grid">
"""
    
    for product in products_sorted:
        html += f"""
        <div class="card">
            <div class="swatch" style="background-color: {product['hex']};"></div>
            <div class="info">
                <div class="brand">{product['brand']}</div>
                <div class="product">{product['product_name']}</div>
                <div class="shade">{product['shade_name']}</div>
                <div class="price">{product['price']}</div>
                <div class="lab">LAB: L={product['L']:.1f}, a={product['a']:.1f}, b={product['b']:.1f}</div>
                <div class="lab">HEX: {product['hex']}</div>
                <div class="color-name">{product['color_name']}</div>
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

def generate_eye_html(products):
    html_path = Path(BASE_DIR) / "eye_color_palette.html"
    
    print(f"아이섀도우 HTML 생성 중: {html_path}")
    
    products_sorted = sorted(products, key=lambda x: x['L'], reverse=True)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>아이섀도우 제품 색상 팔레트</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            padding: 20px; 
            background: linear-gradient(135deg, #ffeef8 0%, #ffe5e5 100%);
            margin: 0;
        }
        h1 { 
            text-align: center; 
            color: #d63384;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #6c757d;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .stats {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); 
            gap: 20px; 
        }
        .card { 
            background: white; 
            padding: 15px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .swatch { 
            width: 100%; 
            height: 120px; 
            border-radius: 8px; 
            margin-bottom: 12px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            border: 2px solid #f0f0f0;
        }
        .info { font-size: 13px; }
        .brand { 
            font-weight: bold; 
            color: #d63384;
            font-size: 14px;
            margin-bottom: 5px;
        }
        .product { 
            color: #495057; 
            font-size: 12px;
            margin-bottom: 5px;
        }
        .shade { 
            color: #212529;
            font-weight: 600;
            margin: 8px 0;
            font-size: 13px;
        }
        .price {
            color: #6c757d;
            font-size: 11px;
            margin-bottom: 8px;
        }
        .lab { 
            color: #868e96; 
            font-family: 'Courier New', monospace; 
            font-size: 11px;
            margin: 3px 0;
        }
        .color-name {
            display: inline-block;
            background: #f8f9fa;
            color: #495057;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>🌸 아이섀도우 제품 색상 팔레트 🌸</h1>
    <div class="subtitle">K-Beauty 아이섀도우 제품 색상 분석 (LAB 색공간 기준)</div>
    
    <div class="stats">
        <strong>총 제품 수:</strong> """ + str(len(products_sorted)) + """ 개
    </div>
    
    <div class="grid">
"""
    
    for product in products_sorted:
        html += f"""
        <div class="card">
            <div class="swatch" style="background-color: {product['hex']};"></div>
            <div class="info">
                <div class="brand">{product['brand']}</div>
                <div class="product">{product['product_name']}</div>
                <div class="shade">{product['shade_name']}</div>
                <div class="price">{product['price']}</div>
                <div class="lab">LAB: L={product['L']:.1f}, a={product['a']:.1f}, b={product['b']:.1f}</div>
                <div class="lab">HEX: {product['hex']}</div>
                <div class="color-name">{product['color_name']}</div>
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
    print("립/아이섀도우 색상 팔레트 HTML 재생성")
    print("="*70)
    print()
    
    lip_products = load_product_data("lip.csv")
    if lip_products:
        generate_lip_html(lip_products)
    
    print()
    
    eye_products = load_product_data("eye.csv")
    if eye_products:
        generate_eye_html(eye_products)
    
    print("\n" + "="*70)
    print("완료!")
    print("="*70)

if __name__ == "__main__":
    main()
