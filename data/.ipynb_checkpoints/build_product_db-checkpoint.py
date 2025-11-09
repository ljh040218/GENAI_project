import sqlite3
import pandas as pd
import glob
import os
import re
from pathlib import Path

class BeautyProductDBBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def create_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                shade_name TEXT NOT NULL,
                price TEXT,
                finish TEXT,
                image_url TEXT,
                swatch_url TEXT,
                L REAL,
                a REAL,
                b REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON products(category)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_brand ON products(brand)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_finish ON products(finish)
        ''')
        
        self.conn.commit()
        print(f"데이터베이스 생성 완료: {self.db_path}")
    
    def _clean_price(self, price_str):
        if pd.isna(price_str):
            return None
        return str(price_str).replace(',', '').replace('원', '').strip()
    
    def _normalize_finish(self, finish_str):
        if pd.isna(finish_str) or finish_str == '':
            return 'unknown'
        
        finish_lower = str(finish_str).lower().strip()
        
        if 'matte' in finish_lower or '매트' in finish_lower:
            return 'matte'
        elif 'shimmer' in finish_lower or '시머' in finish_lower or 'pearl' in finish_lower or '펄' in finish_lower:
            return 'shimmer'
        elif 'glitter' in finish_lower or '글리터' in finish_lower:
            return 'glitter'
        elif 'glossy' in finish_lower or '글로시' in finish_lower or 'shine' in finish_lower:
            return 'glossy'
        else:
            return 'unknown'
    
    def import_csv_files(self, csv_dir: str):
        csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
        
        if not csv_files:
            print(f"CSV 파일을 찾을 수 없습니다: {csv_dir}")
            return
        
        total_count = 0
        
        for csv_file in csv_files:
            print(f"\n처리 중: {os.path.basename(csv_file)}")
            
            try:
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
                
                required_columns = ['brand', 'product_name', 'category', 'shade_name']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    print(f"  경고: 필수 컬럼 누락 {missing_columns}, 스킵")
                    continue
                
                for col in ['price', 'finish', 'image_url', 'swatch_url']:
                    if col not in df.columns:
                        df[col] = None
                
                inserted = 0
                for _, row in df.iterrows():
                    finish = self._normalize_finish(row.get('finish'))
                    
                    self.cursor.execute('''
                        INSERT INTO products 
                        (brand, product_name, category, shade_name, price, finish, image_url, swatch_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['brand'],
                        row['product_name'],
                        row['category'],
                        row['shade_name'],
                        self._clean_price(row.get('price')),
                        finish,
                        row.get('image_url'),
                        row.get('swatch_url')
                    ))
                    inserted += 1
                
                self.conn.commit()
                total_count += inserted
                print(f"  삽입 완료: {inserted}개 제품")
                
            except Exception as e:
                print(f"  에러 발생: {e}")
                continue
        
        print(f"\n총 {total_count}개 제품 데이터베이스에 추가 완료")
    
    def get_statistics(self):
        self.cursor.execute('SELECT COUNT(*) FROM products')
        total = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT category, COUNT(*) FROM products GROUP BY category')
        by_category = self.cursor.fetchall()
        
        self.cursor.execute('SELECT brand, COUNT(*) FROM products GROUP BY brand ORDER BY COUNT(*) DESC LIMIT 10')
        by_brand = self.cursor.fetchall()
        
        self.cursor.execute('SELECT finish, COUNT(*) FROM products GROUP BY finish')
        by_finish = self.cursor.fetchall()
        
        print("\n" + "="*60)
        print("데이터베이스 통계")
        print("="*60)
        print(f"\n총 제품 수: {total}")
        
        print(f"\n카테고리별:")
        for category, count in by_category:
            print(f"  {category}: {count}개")
        
        print(f"\n브랜드별 (상위 10개):")
        for brand, count in by_brand:
            print(f"  {brand}: {count}개")
        
        print(f"\n피니시별:")
        for finish, count in by_finish:
            print(f"  {finish}: {count}개")
        print("="*60)
    
    def export_for_matching(self, output_file: str):
        query = '''
            SELECT 
                id,
                brand,
                product_name,
                shade_name,
                category,
                finish
            FROM products
            WHERE category = 'eye'
        '''
        
        df = pd.read_sql_query(query, self.conn)
        
        df['color'] = df.apply(
            lambda row: {'L': 50, 'a': 0, 'b': 0}, 
            axis=1
        )
        
        products_list = df.to_dict('records')
        
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products_list, f, ensure_ascii=False, indent=2)
        
        print(f"\n매칭용 데이터 export 완료: {output_file}")
        print(f"총 {len(products_list)}개 아이섀도우 제품")
    
    def close(self):
        if self.conn:
            self.conn.close()
            print("\n데이터베이스 연결 종료")


if __name__ == "__main__":
    DB_PATH = "/home/jeongmin/genai/data/db/products.db"
    CSV_DIR = "/home/jeongmin/genai/crawler"
    
    print("=== K-뷰티 제품 데이터베이스 구축 ===\n")
    
    builder = BeautyProductDBBuilder(DB_PATH)
    
    print("1. 데이터베이스 스키마 생성...")
    builder.create_database()
    
    print("\n2. CSV 파일 import...")
    builder.import_csv_files(CSV_DIR)
    
    print("\n3. 통계 출력...")
    builder.get_statistics()
    
    print("\n4. 매칭용 데이터 export...")
    export_path = "/home/jeongmin/genai/data/eyeshadow_products.json"
    builder.export_for_matching(export_path)
    
    builder.close()
    
    print("\n완료!")
