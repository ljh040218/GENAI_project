import csv
import cv2
import numpy as np
import os
from pathlib import Path

BASE_DIR = "/home/jeongmin/genai/data/product"
CHEEK_CSV = "cheek.csv"

def standard_lab_to_opencv(L, a, b):
    L_cv = L * 255 / 100
    a_cv = a + 128
    b_cv = b + 128
    return L_cv, a_cv, b_cv

def opencv_lab_to_rgb(L, a, b):
    lab_pixel = np.uint8([[[L, a, b]]])
    bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)[0][0]
    rgb = (int(bgr_pixel[2]), int(bgr_pixel[1]), int(bgr_pixel[0]))
    return rgb

def standard_lab_to_rgb(L, a, b):
    L_cv, a_cv, b_cv = standard_lab_to_opencv(L, a, b)
    return opencv_lab_to_rgb(L_cv, a_cv, b_cv)

def standard_lab_to_hex(L, a, b):
    r, g, b_val = standard_lab_to_rgb(L, a, b)
    return f"#{r:02x}{g:02x}{b_val:02x}"

def get_color_name(L, a, b):
    if L < 30:
        brightness = "매우 어두운"
    elif L < 50:
        brightness = "어두운"
    elif L < 70:
        brightness = "중간"
    elif L < 85:
        brightness = "밝은"
    else:
        brightness = "매우 밝은"
    
    if abs(a) < 5 and abs(b) < 5:
        return f"{brightness} 무채색"
    
    hue_desc = []
    if a > 15:
        hue_desc.append("빨강")
    elif a < -15:
        hue_desc.append("초록")
    
    if b > 15:
        hue_desc.append("노랑")
    elif b < -15:
        hue_desc.append("파랑")
    
    if len(hue_desc) == 0:
        if abs(a) > abs(b):
            if a > 0:
                return f"{brightness} 핑크/레드"
            else:
                return f"{brightness} 그린"
        else:
            if b > 0:
                return f"{brightness} 옐로우/베이지"
            else:
                return f"{brightness} 블루"
    
    color_str = '+'.join(hue_desc)
    
    if '빨강' in hue_desc and '노랑' in hue_desc:
        if a > 30 and b > 30:
            return f"{brightness} 오렌지"
        elif a > b * 2:
            return f"{brightness} 레드"
        elif b > a * 2:
            return f"{brightness} 옐로우"
        else:
            return f"{brightness} 코랄"
    elif '빨강' in hue_desc and '파랑' in hue_desc:
        return f"{brightness} 퍼플/바이올렛"
    
    return f"{brightness} {color_str}"

def load_cheek_data():
    csv_path = Path(BASE_DIR) / CHEEK_CSV
    
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
                    print(f"[{idx}] {row['brand']} - {row['shade_name']}: LAB 값 없음, 건너뜀")
                    continue
                
                L = float(L_str)
                a = float(a_str)
                b = float(b_str)
                
                if L < -10 or L > 110 or abs(a) > 150 or abs(b) > 150:
                    print(f"[{idx}] {row['brand']} - {row['shade_name']}: LAB 값 범위 이상 (L={L}, a={a}, b={b}), 건너뜀")
                    continue
                
                hex_code = standard_lab_to_hex(L, a, b)
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
                    'color_name': color_name,
                    'color_hex_original': row.get('color_hex', '')
                })
                
                print(f"[{idx}] {row['brand']} - {row['shade_name']}: L={L:.1f}, a={a:.1f}, b={b:.1f} → {hex_code}")
                
            except (ValueError, KeyError) as e:
                print(f"[{idx}] 오류: {e}, 건너뜀")
                continue
    
    print(f"\n총 {len(products)}개 제품 로드 완료\n")
    return products

def generate_html(products):
    html_path = Path(BASE_DIR) / "cheek_color_palette.html"
    
    print(f"HTML 생성 중: {html_path}")
    
    products_sorted = sorted(products, key=lambda x: x['L'], reverse=True)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>치크 제품 색상 팔레트</title>
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
    <h1>🌸 치크 제품 색상 팔레트 🌸</h1>
    <div class="subtitle">K-Beauty 치크 제품 색상 분석 (LAB 색공간 기준)</div>
    
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
    print(f"브라우저로 열어서 확인하세요!")

def main():
    print("="*70)
    print("치크 제품 색상 팔레트 HTML 생성")
    print("="*70)
    print()
    
    products = load_cheek_data()
    
    if products:
        generate_html(products)
        print("\n" + "="*70)
        print("완료!")
        print("="*70)
    else:
        print("제품 데이터가 없습니다.")

if __name__ == "__main__":
    main()
