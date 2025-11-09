import sqlite3
import json
from typing import List, Dict, Optional

class ProductDBLoader:
    def __init__(self, db_path: str = "/home/jeongmin/genai/data/db/products.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def load_products_by_category(self, category: str, finish_filter: Optional[List[str]] = None) -> List[Dict]:
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        if finish_filter:
            placeholders = ','.join(['?' for _ in finish_filter])
            query = f'''
                SELECT 
                    id, brand, product_name, shade_name, 
                    category, finish, price, image_url, swatch_url,
                    L, a, b
                FROM products
                WHERE category = ? AND finish IN ({placeholders})
            '''
            params = [category] + finish_filter
        else:
            query = '''
                SELECT 
                    id, brand, product_name, shade_name, 
                    category, finish, price, image_url, swatch_url,
                    L, a, b
                FROM products
                WHERE category = ?
            '''
            params = [category]
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        products = []
        for row in rows:
            product = {
                'id': row['id'],
                'brand': row['brand'],
                'product_name': row['product_name'],
                'color_name': row['shade_name'],
                'finish': row['finish'] if row['finish'] else 'unknown',
                'price': row['price'],
                'image_url': row['image_url'],
                'swatch_url': row['swatch_url'],
                'color': {
                    'L': row['L'] if row['L'] else 50.0,
                    'a': row['a'] if row['a'] else 0.0,
                    'b': row['b'] if row['b'] else 0.0
                }
            }
            products.append(product)
        
        return products
    
    def load_eyeshadow_products(self) -> List[Dict]:
        return self.load_products_by_category('eye')
    
    def load_lip_products(self) -> List[Dict]:
        return self.load_products_by_category('lip')
    
    def load_cheek_products(self) -> List[Dict]:
        return self.load_products_by_category('cheek')
    
    def load_all_for_matcher(self) -> Dict[str, List[Dict]]:
        return {
            'lips': self.load_lip_products(),
            'cheeks': self.load_cheek_products(),
            'eyeshadow': self.load_eyeshadow_products()
        }
    
    def get_product_count(self, category: Optional[str] = None) -> int:
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        if category:
            cursor.execute('SELECT COUNT(*) FROM products WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT COUNT(*) FROM products')
        
        return cursor.fetchone()[0]


if __name__ == "__main__":
    print("=== 제품 DB 로더 테스트 ===\n")
    
    loader = ProductDBLoader()
    loader.connect()
    
    print(f"전체 제품 수: {loader.get_product_count()}")
    print(f"아이섀도우 제품 수: {loader.get_product_count('eye')}\n")
    
    print("아이섀도우 제품 로드 (상위 5개):")
    eyeshadow_products = loader.load_eyeshadow_products()
    for i, product in enumerate(eyeshadow_products[:5], 1):
        print(f"\n{i}. {product['brand']} - {product['product_name']}")
        print(f"   색상: {product['color_name']}")
        print(f"   피니시: {product['finish']}")
        print(f"   LAB: L={product['color']['L']}, a={product['color']['a']}, b={product['color']['b']}")
    
    print(f"\n\n총 로드된 아이섀도우: {len(eyeshadow_products)}개")
    
    loader.close()
    
    print("\n=== 테스트 완료 ===")
