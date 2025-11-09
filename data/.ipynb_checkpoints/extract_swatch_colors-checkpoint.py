import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import sqlite3
from typing import Dict, Optional, Tuple
import time

class SwatchColorExtractor:
    def __init__(self, db_path: str = "/home/jeongmin/genai/data/db/products.db"):
        self.db_path = db_path
        self.conn = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def connect_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close_db(self):
        if self.conn:
            self.conn.close()
    
    def download_image(self, url: str, timeout: int = 10) -> Optional[np.ndarray]:
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            img_rgb = img.convert('RGB')
            img_array = np.array(img_rgb)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
        
        except Exception as e:
            print(f"  이미지 다운로드 실패: {e}")
            return None
    
    def extract_center_region(self, image: np.ndarray, center_ratio: float = 0.4) -> np.ndarray:
        h, w = image.shape[:2]
        
        center_h = int(h * center_ratio)
        center_w = int(w * center_ratio)
        
        y1 = (h - center_h) // 2
        y2 = y1 + center_h
        x1 = (w - center_w) // 2
        x2 = x1 + center_w
        
        return image[y1:y2, x1:x2]
    
    def extract_dominant_color_kmeans(self, image: np.ndarray, k: int = 3) -> Tuple[float, float, float]:
        pixels = image.reshape(-1, 3).astype(np.float32)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
        
        counts = np.bincount(labels.flatten())
        dominant_idx = np.argmax(counts)
        dominant_bgr = centers[dominant_idx]
        
        lab = cv2.cvtColor(np.uint8([[dominant_bgr]]), cv2.COLOR_BGR2LAB)[0][0]
        
        return float(lab[0]), float(lab[1]), float(lab[2])
    
    def extract_color_spatial_center(self, image: np.ndarray) -> Tuple[float, float, float]:
        center_region = self.extract_center_region(image, center_ratio=0.5)
        
        h, w = center_region.shape[:2]
        kernel_size = max(5, int(0.03 * min(h, w)))
        eroded = cv2.erode(center_region, np.ones((kernel_size, kernel_size), np.uint8), iterations=1)
        
        if eroded.size == 0:
            eroded = center_region
        
        lab = cv2.cvtColor(eroded, cv2.COLOR_BGR2LAB)
        mean_lab = cv2.mean(lab)[:3]
        
        return mean_lab
    
    def extract_color_high_saturation(self, image: np.ndarray, top_percent: float = 0.3) -> Tuple[float, float, float]:
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
    
    def extract_color_auto(self, image: np.ndarray) -> Dict:
        method1 = self.extract_color_spatial_center(image)
        method2 = self.extract_color_high_saturation(image)
        method3 = self.extract_dominant_color_kmeans(image, k=3)
        
        final_L = (method1[0] + method2[0] + method3[0]) / 3
        final_a = (method1[1] + method2[1] + method3[1]) / 3
        final_b = (method1[2] + method2[2] + method3[2]) / 3
        
        return {
            'L': round(final_L, 2),
            'a': round(final_a, 2),
            'b': round(final_b, 2),
            'method1_spatial': method1,
            'method2_saturation': method2,
            'method3_kmeans': method3
        }
    
    def update_product_color(self, product_id: int, L: float, a: float, b: float):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET L = ?, a = ?, b = ?
            WHERE id = ?
        ''', (L, a, b, product_id))
        self.conn.commit()
    
    def process_all_products(self, limit: Optional[int] = None, delay: float = 0.5):
        if not self.conn:
            self.connect_db()
        
        cursor = self.conn.cursor()
        
        if limit:
            cursor.execute('''
                SELECT id, brand, product_name, shade_name, swatch_url
                FROM products
                WHERE swatch_url IS NOT NULL AND swatch_url != ''
                LIMIT ?
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT id, brand, product_name, shade_name, swatch_url
                FROM products
                WHERE swatch_url IS NOT NULL AND swatch_url != ''
            ''')
        
        products = cursor.fetchall()
        total = len(products)
        
        print(f"처리할 제품: {total}개\n")
        
        success_count = 0
        fail_count = 0
        
        for i, product in enumerate(products, 1):
            print(f"[{i}/{total}] {product['brand']} - {product['shade_name']}")
            
            image = self.download_image(product['swatch_url'])
            
            if image is None:
                print(f"  실패: 이미지 다운로드 불가\n")
                fail_count += 1
                continue
            
            try:
                color_data = self.extract_color_auto(image)
                
                self.update_product_color(
                    product['id'],
                    color_data['L'],
                    color_data['a'],
                    color_data['b']
                )
                
                print(f"  성공: L={color_data['L']}, a={color_data['a']}, b={color_data['b']}\n")
                success_count += 1
                
            except Exception as e:
                print(f"  실패: {e}\n")
                fail_count += 1
            
            time.sleep(delay)
        
        print("\n" + "="*60)
        print(f"처리 완료: 성공 {success_count}개, 실패 {fail_count}개")
        print("="*60)
    
    def process_single_product(self, product_id: int) -> Optional[Dict]:
        if not self.conn:
            self.connect_db()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, brand, product_name, shade_name, swatch_url
            FROM products
            WHERE id = ?
        ''', (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            print(f"제품을 찾을 수 없습니다: ID {product_id}")
            return None
        
        if not product['swatch_url']:
            print(f"스와치 이미지가 없습니다: {product['brand']} {product['shade_name']}")
            return None
        
        print(f"처리 중: {product['brand']} - {product['shade_name']}")
        
        image = self.download_image(product['swatch_url'])
        
        if image is None:
            return None
        
        color_data = self.extract_color_auto(image)
        
        self.update_product_color(
            product['id'],
            color_data['L'],
            color_data['a'],
            color_data['b']
        )
        
        print(f"완료: L={color_data['L']}, a={color_data['a']}, b={color_data['b']}")
        
        return color_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='스와치 이미지에서 LAB 색상 추출')
    parser.add_argument('--limit', type=int, default=None, help='처리할 제품 수 제한')
    parser.add_argument('--delay', type=float, default=0.5, help='요청 간 대기 시간(초)')
    parser.add_argument('--product-id', type=int, default=None, help='특정 제품 ID만 처리')
    
    args = parser.parse_args()
    
    print("=== 스와치 이미지 색상 추출 ===\n")
    
    extractor = SwatchColorExtractor()
    extractor.connect_db()
    
    if args.product_id:
        extractor.process_single_product(args.product_id)
    else:
        extractor.process_all_products(limit=args.limit, delay=args.delay)
    
    extractor.close_db()
    
    print("\n완료!")