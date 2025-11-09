import sqlite3
import sys

def check_db_lab_values(db_path='/home/jeongmin/genai/data/db/products.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("="*70)
        print("제품 DB LAB 값 확인")
        print("="*70)
        
        cursor.execute('SELECT COUNT(*) FROM products')
        total_count = cursor.fetchone()[0]
        print(f"\n총 제품 수: {total_count}개")
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE L IS NOT NULL AND L != 50.0')
        updated_count = cursor.fetchone()[0]
        print(f"업데이트된 제품: {updated_count}개")
        print(f"업데이트 안된 제품: {total_count - updated_count}개")
        
        if updated_count > 0:
            cursor.execute('''
                SELECT AVG(L), AVG(a), AVG(b), 
                       MIN(L), MAX(L),
                       MIN(a), MAX(a),
                       MIN(b), MAX(b)
                FROM products 
                WHERE L IS NOT NULL AND L != 50.0
            ''')
            stats = cursor.fetchone()
            
            print(f"\n=== LAB 통계 (업데이트된 제품만) ===")
            print(f"평균: L={stats[0]:.2f}, a={stats[1]:.2f}, b={stats[2]:.2f}")
            print(f"L 범위: {stats[3]:.2f} ~ {stats[4]:.2f}")
            print(f"a 범위: {stats[5]:.2f} ~ {stats[6]:.2f}")
            print(f"b 범위: {stats[7]:.2f} ~ {stats[8]:.2f}")
        
        print(f"\n=== 샘플 제품 (업데이트된 것) ===")
        cursor.execute('''
            SELECT id, brand, product_name, shade_name, L, a, b
            FROM products
            WHERE L IS NOT NULL AND L != 50.0
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"\n[ID: {row[0]}] {row[1]} - {row[2]}")
                print(f"  색상: {row[3]}")
                print(f"  LAB: L={row[4]:.2f}, a={row[5]:.2f}, b={row[6]:.2f}")
        else:
            print("업데이트된 제품이 없습니다.")
        
        print(f"\n=== 기본값 제품 (업데이트 안된 것) ===")
        cursor.execute('''
            SELECT id, brand, product_name, shade_name, L, a, b
            FROM products
            WHERE L IS NULL OR L = 50.0
            LIMIT 5
        ''')
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"\n[ID: {row[0]}] {row[1]} - {row[2]}")
                print(f"  색상: {row[3]}")
                print(f"  LAB: L={row[4]}, a={row[5]}, b={row[6]} (기본값)")
        else:
            print("모든 제품이 업데이트되었습니다!")
        
        print(f"\n=== LAB 값 이상치 확인 ===")
        cursor.execute('''
            SELECT id, brand, shade_name, L, a, b
            FROM products
            WHERE L < 0 OR L > 100 OR ABS(a) > 128 OR ABS(b) > 128
        ''')
        
        outliers = cursor.fetchall()
        if outliers:
            print("경고: LAB 범위를 벗어난 제품 발견!")
            for row in outliers:
                print(f"  [ID: {row[0]}] {row[1]} {row[2]}: L={row[3]}, a={row[4]}, b={row[5]}")
        else:
            print("정상: 모든 LAB 값이 유효 범위 내에 있습니다.")
        
        print("\n" + "="*70)
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"DB 에러: {e}")
        return False
    except Exception as e:
        print(f"에러: {e}")
        return False


def check_specific_product(product_id, db_path='/home/jeongmin/genai/data/db/products.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, brand, product_name, shade_name, L, a, b, swatch_url
            FROM products
            WHERE id = ?
        ''', (product_id,))
        
        row = cursor.fetchone()
        
        if row:
            print("="*70)
            print(f"제품 상세 정보 [ID: {row[0]}]")
            print("="*70)
            print(f"브랜드: {row[1]}")
            print(f"제품명: {row[2]}")
            print(f"색상명: {row[3]}")
            print(f"\nLAB 값:")
            print(f"  L = {row[4]} (밝기: 0=검정, 100=흰색)")
            print(f"  a = {row[5]} (음수=초록, 양수=빨강)")
            print(f"  b = {row[6]} (음수=파랑, 양수=노랑)")
            
            if row[4] == 50.0 and row[5] == 0.0 and row[6] == 0.0:
                print("\n상태: 기본값 (아직 업데이트 안됨)")
            else:
                print("\n상태: 업데이트됨")
            
            if row[7]:
                print(f"\n스와치 URL: {row[7][:80]}...")
            else:
                print("\n스와치 URL: 없음")
            
            print("="*70)
        else:
            print(f"제품을 찾을 수 없습니다: ID {product_id}")
        
        conn.close()
        
    except Exception as e:
        print(f"에러: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='제품 DB LAB 값 확인')
    parser.add_argument('--db', default='/home/jeongmin/genai/data/db/products.db', 
                       help='DB 파일 경로')
    parser.add_argument('--product-id', type=int, help='특정 제품 ID 확인')
    
    args = parser.parse_args()
    
    if args.product_id:
        check_specific_product(args.product_id, args.db)
    else:
        check_db_lab_values(args.db)