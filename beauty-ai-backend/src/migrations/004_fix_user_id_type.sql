ALTER TABLE feedback_embeddings 
  ALTER COLUMN user_id TYPE VARCHAR(255) 
  USING user_id::VARCHAR(255);

ALTER TABLE feedback_embeddings 
  ALTER COLUMN feedback_id TYPE VARCHAR(255) 
  USING feedback_id::VARCHAR(255);

COMMENT ON COLUMN feedback_embeddings.user_id IS 'Frontend string user_id (e.g., user_12345)';
COMMENT ON COLUMN feedback_embeddings.feedback_id IS 'Feedback identifier from main database';

DROP INDEX IF EXISTS idx_feedback_embeddings_user;
CREATE INDEX idx_feedback_embeddings_user ON feedback_embeddings(user_id);

DROP INDEX IF EXISTS idx_feedback_embeddings_feedback;
CREATE INDEX idx_feedback_embeddings_feedback ON feedback_embeddings(feedback_id);

DROP INDEX IF EXISTS idx_feedback_user_created;
CREATE INDEX idx_feedback_user_created ON feedback_embeddings(user_id, created_at DESC);