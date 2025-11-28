import os
import pandas as pd
import psycopg2
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('/home/jeongmin/genai/beauty-ai-python/app/.env')

VECTOR_DB_URL = os.getenv("VECTOR_DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not VECTOR_DB_URL or not OPENAI_API_KEY:
    print("❌ 환경변수 로드 실패")
    print(f"VECTOR_DB_URL: {VECTOR_DB_URL}")
    print(f"OPENAI_API_KEY: {'설정됨' if OPENAI_API_KEY else '없음'}")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def upload_csv_to_db(csv_file_path, category_name):
    print(f"\n{category_name} 데이터 처리 시작: {csv_file_path}")
    
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"파일 읽기 실패: {csv_file_path} - {e}")
        return

    if 'product_id' not in df.columns:
        print(f"❌ product_id 컬럼이 없습니다.")
        return
    
    df_valid = df[df['product_id'].notna()].copy()
    
    if len(df_valid) == 0:
        print(f"❌ 매칭된 제품이 없습니다.")
        return
    
    print(f"총 {len(df)}개 중 {len(df_valid)}개 처리")

    conn = psycopg2.connect(VECTOR_DB_URL)
    cur = conn.cursor()
    
    success_count = 0

    for idx, row in df_valid.iterrows():
        try:
            product_id = row['product_id']
            
            rag_text = (
                f"제품명: {row['brand']} {row['product_name']} ({row['color_name']})\n"
                f"퍼스널컬러: {row['personal_color']}\n"
                f"색상 특징: {row['color_detail']}\n"
                f"텍스처: {row['texture_tag']}\n"
                f"장점 요약: {row['pros_summary']}\n"
                f"단점/주의사항: {row['cons_summary']}\n"
                f"주요 성분: {row['key_ingredients']}"
            )

            metadata = {
                "personal_color": row['personal_color'],
                "texture": row['texture_tag'],
                "detail": row['color_detail'],
                "ingredients": row['key_ingredients']
            }

            vector = get_embedding(rag_text)

            cur.execute("""
                INSERT INTO product_embeddings 
                (id, category, brand, product_name, color_name, price, text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
            """, (
                product_id,
                category_name,
                row['brand'],
                row['product_name'],
                row['color_name'],
                int(row['price']),
                rag_text,
                json.dumps(metadata, ensure_ascii=False),
                vector
            ))
            
            success_count += 1
            if success_count % 10 == 0:
                print(f"   -> {success_count}개 저장 완료...")

        except Exception as e:
            print(f"   에러 ({row['product_name']}): {e}")

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ {category_name} 완료: {success_count}개\n")


if __name__ == "__main__":
    upload_csv_to_db("lip_dataset_with_id.csv", "lips")
    upload_csv_to_db("cheek_dataset_with_id.csv", "cheeks")
    upload_csv_to_db("eyeshadow_dataset_with_id.csv", "eyes")
    
    print("="*60)
    print("전체 업로드 완료!")
    print("="*60)