-- 제품 정보를 담을 벡터 테이블 생성
CREATE TABLE IF NOT EXISTS product_embeddings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  category VARCHAR(50),
  brand VARCHAR(100),
  product_name VARCHAR(200),
  color_name VARCHAR(100),
  price INTEGER,
  text TEXT,
  metadata JSONB,
  embedding vector(1536),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 검색 속도 향상을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_product_vec 
ON product_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 카테고리별 인덱스
CREATE INDEX IF NOT EXISTS idx_product_category 
ON product_embeddings(category);

-- 브랜드별 인덱스
CREATE INDEX IF NOT EXISTS idx_product_brand 
ON product_embeddings(brand);

-- 가격대 검색용 인덱스
CREATE INDEX IF NOT EXISTS idx_product_price 
ON product_embeddings(price);

-- 메타데이터 검색용 GIN 인덱스
CREATE INDEX IF NOT EXISTS idx_product_metadata 
ON product_embeddings USING GIN(metadata);

-- 코멘트
COMMENT ON TABLE product_embeddings IS '제품 정보 벡터 임베딩 저장소 (RAG용)';
COMMENT ON COLUMN product_embeddings.text IS 'RAG가 읽을 핵심 텍스트 덩어리 (리뷰, 특징 등)';
COMMENT ON COLUMN product_embeddings.metadata IS '필터링용 데이터 (퍼스널컬러, 텍스처, finish 등)';
COMMENT ON COLUMN product_embeddings.embedding IS 'OpenAI text-embedding-3-small (1536차원)';