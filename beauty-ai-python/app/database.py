import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
import os


def get_db_connection(database_url: str):
    return psycopg2.connect(database_url)


def get_products_from_db(database_url: str, category: str) -> List[Dict]:
    """
    PostgreSQL에서 특정 카테고리의 모든 제품을 가져옴
    """
    try:
        conn = get_db_connection(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT id, brand, name, category, price, finish,
                   color_rgb, color_lab, color_hex, image_url,
                   description, purchase_links, created_at
            FROM products
            WHERE category = %s
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (category,))
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [dict(p) for p in products]
        
    except Exception as e:
        print(f"Database error: {e}")
        return []


def get_product_by_id(database_url: str, product_id: str) -> Optional[Dict]:
    """
    특정 ID의 제품 조회
    """
    try:
        conn = get_db_connection(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT * FROM products WHERE id = %s
        """
        
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return dict(product) if product else None
        
    except Exception as e:
        print(f"Database error: {e}")
        return None