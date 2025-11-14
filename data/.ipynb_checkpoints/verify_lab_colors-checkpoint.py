import cv2
import numpy as np
import sqlite3
from typing import List, Tuple, Optional
import os

class LABColorVerifier:
    def __init__(self, db_path: str = "/home/jeongmin/genai/data/db/products.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close_db(self):
        if self.conn:
            self.conn.close()
    
    def lab_to_rgb(self, L: float, a: float, b: float) -> Tuple[int, int, int]:
        lab_pixel = np.uint8([[[L, a, b]]])
        bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)[0][0]
        rgb = (int(bgr_pixel[2]), int(bgr_pixel[1]), int(bgr_pixel[0]))
        return rgb
    
    def lab_to_hex(self, L: float, a: float, b: float) -> str:
        r, g, b_val = self.lab_to_rgb(L, a, b)
        return f"#{r:02x}{g:02x}{b_val:02x}"
    
    def get_color_name(self, L: float, a: float, b: float) -> str:
        if L < 30:
            return "매우 어두운"
        elif L > 80:
            return "매우 밝은"
        
        if abs(a) < 10 and abs(b) < 10:
            return "무채색/베이지"
        
        if a > 20:
            red_component = "빨강"
        elif a < -20:
            red_component = "초록"
        else:
            red_component = ""
        
        if b > 20:
            yellow_component = "노랑"
        elif b < -20:
            yellow_component = "파랑"
        else:
            yellow_component = ""
        
        if red_component and yellow_component:
            if a > 30 and b < 20:
                return "빨강"
            elif a > 20 and b > 30:
                return "오렌지"
            elif abs(a) < 20 and b > 30:
                return "노랑"
            elif a < -20 and b > 20:
                return "연두"
            elif a < -30 and abs(b) < 20:
                return "초록"
            elif a < -20 and b < -20:
                return "청록"
            elif abs(a) < 20 and b < -30:
                return "파랑"
            elif a > 20 and b < -20:
                return "보라"
            else:
                return f"{red_component}+{yellow_component}"
        elif red_component:
            return red_component
        elif yellow_component:
            return yellow_component
        else:
            return "중성"
    
    def create_color_swatch(self, L: float, a: float, b: float, 
                          size: int = 100) -> np.ndarray:
        swatch = np.zeros((size, size, 3), dtype=np.uint8)
        lab_img = np.full((size, size, 3), [L, a, b], dtype=np.uint8)
        bgr_img = cv2.cvtColor(lab_img, cv2.COLOR_LAB2BGR)
        return bgr_img
    
    def verify_product_colors(self, limit: int = 10, 
                            save_images: bool = True,
                            output_dir: str = "/home/jeongmin/genai/output/lab_verification"):
        if not self.conn:
            self.connect_db()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, brand, product_name, shade_name, L, a, b
            FROM products
            WHERE L IS NOT NULL
            LIMIT ?
        ''', (limit,))
        
        products = cursor.fetchall()
        
        if save_images and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        print("="*80)
        print("LAB 색상 검증 결과")
        print("="*80)
        
        for i, product in enumerate(products, 1):
            L, a, b = product['L'], product['a'], product['b']
            
            rgb = self.lab_to_rgb(L, a, b)
            hex_code = self.lab_to_hex(L, a, b)
            color_name = self.get_color_name(L, a, b)
            
            print(f"\n[{i}/{len(products)}] {product['brand']} - {product['shade_name']}")
            print(f"  LAB: L={L:.2f}, a={a:.2f}, b={b:.2f}")
            print(f"  RGB: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}")
            print(f"  HEX: {hex_code}")
            print(f"  색상: {color_name}")
            
            if save_images:
                swatch = self.create_color_swatch(L, a, b, size=200)
                
                filename = f"{product['id']}_{product['brand']}_{product['shade_name']}.png"
                filename = filename.replace('/', '_').replace(' ', '_')
                filepath = os.path.join(output_dir, filename)
                
                cv2.imwrite(filepath, swatch)
                print(f"  저장: {filepath}")
        
        print("\n" + "="*80)
    
    def compare_with_original_swatch(self, product_id: int, 
                                    swatch_image_path: str):
        if not self.conn:
            self.connect_db()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT brand, shade_name, L, a, b
            FROM products
            WHERE id = ?
        ''', (product_id,))
        
        product = cursor.fetchone()
        if not product:
            print(f"제품을 찾을 수 없습니다: ID {product_id}")
            return
        
        original_img = cv2.imread(swatch_image_path)
        if original_img is None:
            print(f"이미지를 불러올 수 없습니다: {swatch_image_path}")
            return
        
        L, a, b = product['L'], product['a'], product['b']
        extracted_swatch = self.create_color_swatch(L, a, b, 
                                                    size=original_img.shape[0])
        
        comparison = np.hstack([original_img, extracted_swatch])
        
        cv2.imshow('원본 vs 추출된 색상', comparison)
        print("\n비교 이미지가 표시됩니다. 아무 키나 눌러 종료하세요.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def check_color_distribution(self):
        if not self.conn:
            self.connect_db()
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(L) as avg_L,
                MIN(L) as min_L,
                MAX(L) as max_L,
                AVG(ABS(a)) as avg_a,
                AVG(ABS(b)) as avg_b
            FROM products
            WHERE L IS NOT NULL
        ''')
        
        stats = cursor.fetchone()
        
        print("\n" + "="*80)
        print("전체 색상 통계")
        print("="*80)
        print(f"총 제품 수: {stats['total']}개")
        print(f"\nL (밝기) 범위: {stats['min_L']:.2f} ~ {stats['max_L']:.2f}")
        print(f"  평균: {stats['avg_L']:.2f}")
        print(f"\na (빨강-초록) 평균 절대값: {stats['avg_a']:.2f}")
        print(f"b (노랑-파랑) 평균 절대값: {stats['avg_b']:.2f}")
        
        cursor.execute('''
            SELECT brand, shade_name, L, a, b
            FROM products
            WHERE L IS NOT NULL AND (L < 0 OR L > 100 OR ABS(a) > 128 OR ABS(b) > 128)
        ''')
        
        outliers = cursor.fetchall()
        if outliers:
            print("\n⚠ 범위 밖 값 발견:")
            for row in outliers:
                print(f"  {row['brand']} {row['shade_name']}: L={row['L']}, a={row['a']}, b={row['b']}")
        else:
            print("\n✓ 모든 값이 정상 범위 내에 있습니다.")
        
        print("="*80)
    
    def generate_color_palette_html(self, output_file: str = "/home/jeongmin/genai/output/color_palette.html"):
        if not self.conn:
            self.connect_db()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, brand, product_name, shade_name, L, a, b
            FROM products
            WHERE L IS NOT NULL
            ORDER BY L DESC, a, b
        ''')
        
        products = cursor.fetchall()
        
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>제품 색상 팔레트</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        h1 { text-align: center; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .card { background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .swatch { width: 100%; height: 100px; border-radius: 4px; margin-bottom: 10px; }
        .info { font-size: 12px; }
        .brand { font-weight: bold; color: #333; }
        .shade { color: #666; margin: 5px 0; }
        .lab { color: #999; font-family: monospace; font-size: 11px; }
    </style>
</head>
<body>
    <h1>제품 색상 팔레트 검증</h1>
    <div class="grid">
"""
        
        for product in products:
            L, a, b = product['L'], product['a'], product['b']
            hex_code = self.lab_to_hex(L, a, b)
            color_name = self.get_color_name(L, a, b)
            
            html += f"""
        <div class="card">
            <div class="swatch" style="background-color: {hex_code};"></div>
            <div class="info">
                <div class="brand">{product['brand']}</div>
                <div class="shade">{product['shade_name']}</div>
                <div class="lab">LAB: {L:.1f}, {a:.1f}, {b:.1f}</div>
                <div class="lab">{hex_code} · {color_name}</div>
            </div>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✓ HTML 팔레트 생성 완료: {output_file}")
        print("  브라우저로 열어서 모든 제품의 색상을 확인하세요!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LAB 색상 검증')
    parser.add_argument('--limit', type=int, default=10, help='확인할 제품 수')
    parser.add_argument('--stats', action='store_true', help='통계만 출력')
    parser.add_argument('--html', action='store_true', help='HTML 팔레트 생성')
    parser.add_argument('--no-images', action='store_true', help='이미지 저장 안 함')
    
    args = parser.parse_args()
    
    verifier = LABColorVerifier()
    verifier.connect_db()
    
    if args.stats:
        verifier.check_color_distribution()
    elif args.html:
        verifier.generate_color_palette_html()
    else:
        verifier.verify_product_colors(
            limit=args.limit,
            save_images=not args.no_images
        )
    
    verifier.close_db()
    
    print("\n완료!")
