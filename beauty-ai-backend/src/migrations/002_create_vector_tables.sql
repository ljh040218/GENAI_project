-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 피드백 임베딩 테이블 (벡터 전용)
CREATE TABLE IF NOT EXISTS feedback_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feedback_id UUID NOT NULL,
  user_id UUID NOT NULL,
  embedding vector(1536),
  text TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 벡터 인덱스 (코사인 유사도 검색용)
CREATE INDEX IF NOT EXISTS idx_embedding_vector 
ON feedback_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 일반 인덱스
CREATE INDEX IF NOT EXISTS idx_feedback_embeddings_feedback ON feedback_embeddings(feedback_id);
CREATE INDEX IF NOT EXISTS idx_feedback_embeddings_user ON feedback_embeddings(user_id);