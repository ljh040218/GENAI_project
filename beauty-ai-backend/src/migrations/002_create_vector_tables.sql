-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 피드백 임베딩 테이블 (벡터 전용)
CREATE TABLE IF NOT EXISTS feedback_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feedback_id VARCHAR(255) NOT NULL,
  user_id VARCHAR(255) NOT NULL,
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
CREATE INDEX IF NOT EXISTS idx_feedback_embeddings_created ON feedback_embeddings(created_at DESC);

-- 사용자별 피드백 조회 성능 향상
CREATE INDEX IF NOT EXISTS idx_feedback_user_created 
ON feedback_embeddings(user_id, created_at DESC);

-- 코멘트 추가
COMMENT ON TABLE feedback_embeddings IS 'RAG 시스템을 위한 사용자 피드백 벡터 임베딩 저장소';
COMMENT ON COLUMN feedback_embeddings.embedding IS 'OpenAI text-embedding-3-small 모델 (1536 차원)';
COMMENT ON COLUMN feedback_embeddings.metadata IS 'intent, preferences, category 등 추가 정보';