import cv2
import numpy as np
from typing import Dict, Tuple
import os
import sqlite3

class LocalSwatchColorExtractor:
    def __init__(self, db_path: str = "/home/jeongmin/genai/data/db/products.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close_db(self):
        if self.conn:
            self.conn.close()
    
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
            'method1_spatial': {
                'L': round(method1[0], 2),
                'a': round(method1[1], 2),
                'b': round(method1[2], 2)
            },
            'method2_saturation': {
                'L': round(method2[0], 2),
                'a': round(method2[1], 2),
                'b': round(method2[2], 2)
            },
            'method3_kmeans': {
                'L': round(method3[0], 2),
                'a': round(method3[1], 2),
                'b': round(method3[2], 2)
            }
        }
    
    def process_image_file(self, image_path: str) -> Dict:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")
        
        print(f"이미지 크기: {image.shape[1]}x{image.shape[0]}")
        
        result = self.extract_color_auto(image)
        
        return result
    
    def update_product_color(self, product_id: int, L: float, a: float, b: float):
        if not self.conn:
            self.connect_db()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET L = ?, a = ?, b = ?
            WHERE id = ?
        ''', (L, a, b, product_id))
        self.conn.commit()
        print(f"DB 업데이트 완료: 제품 ID {product_id}")
    
    def process_and_update(self, product_id: int, image_path: str):
        result = self.process_image_file(image_path)
        
        self.update_product_color(product_id, result['L'], result['a'], result['b'])
        
        return result


if __name__ == "__main__":
    print("=== 로컬 이미지 색상 추출 테스트 ===\n")
    
    extractor = LocalSwatchColorExtractor()
    
    test_image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    center = test_image[60:140, 60:140]
    center[:, :] = [30, 80, 200]
    
    print("더미 이미지 생성 완료 (빨강 계열)\n")
    
    result = extractor.extract_color_auto(test_image)
    
    print("추출 결과:")
    print(f"  최종 LAB: L={result['L']}, a={result['a']}, b={result['b']}\n")
    print("방법별 결과:")
    print(f"  1. 공간적 중심:      L={result['method1_spatial']['L']}, a={result['method1_spatial']['a']}, b={result['method1_spatial']['b']}")
    print(f"  2. 고채도 픽셀:      L={result['method2_saturation']['L']}, a={result['method2_saturation']['a']}, b={result['method2_saturation']['b']}")
    print(f"  3. K-means 클러스터: L={result['method3_kmeans']['L']}, a={result['method3_kmeans']['a']}, b={result['method3_kmeans']['b']}")
    
    print("\n" + "="*60)
    print("사용 예시")
    print("="*60)
    
    print("\n1. 이미지 파일에서 색상 추출:")
    print("  extractor = LocalSwatchColorExtractor()")
    print("  result = extractor.process_image_file('/path/to/swatch.jpg')")
    print("  print(f\"LAB: {result['L']}, {result['a']}, {result['b']}\")")
    
    print("\n2. 이미지 추출 + DB 업데이트:")
    print("  extractor = LocalSwatchColorExtractor()")
    print("  extractor.connect_db()")
    print("  result = extractor.process_and_update(")
    print("      product_id=1,")
    print("      image_path='/home/jeongmin/genai/data/swatches/product1.jpg'")
    print("  )")
    print("  extractor.close_db()")
    
    print("\n3. 배치 처리:")
    print("  import os")
    print("  extractor = LocalSwatchColorExtractor()")
    print("  extractor.connect_db()")
    print("  swatch_dir = '/home/jeongmin/genai/data/swatches'")
    print("  for filename in os.listdir(swatch_dir):")
    print("      if filename.endswith('.jpg'):")
    print("          product_id = int(filename.split('_')[0])")
    print("          image_path = os.path.join(swatch_dir, filename)")
    print("          extractor.process_and_update(product_id, image_path)")
    print("  extractor.close_db()")
    
    print("\n" + "="*60)