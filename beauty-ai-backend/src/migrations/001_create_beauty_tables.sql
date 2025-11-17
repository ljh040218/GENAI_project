-- 1. 뷰티 프로필 테이블
CREATE TABLE IF NOT EXISTS beauty_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  personal_color VARCHAR(20) NOT NULL CHECK (personal_color IN ('warm', 'cool', 'neutral')),
  preferred_finish VARCHAR(20) NOT NULL CHECK (preferred_finish IN ('matte', 'glossy', 'satin')),
  preferred_store VARCHAR(20) NOT NULL CHECK (preferred_store IN ('roadshop', 'department')),
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id)
);

-- 2. 제품 테이블
CREATE TABLE IF NOT EXISTS products (
  id VARCHAR(50) PRIMARY KEY,
  brand VARCHAR(100) NOT NULL,
  name VARCHAR(200) NOT NULL,
  category VARCHAR(20) NOT NULL CHECK (category IN ('lips', 'cheeks', 'eyes')),
  price INTEGER NOT NULL CHECK (price > 0),
  finish VARCHAR(20) CHECK (finish IN ('matte', 'glossy', 'satin', 'velvet')),
  color_rgb INTEGER[3],
  color_lab FLOAT[3],
  color_hex VARCHAR(7),
  image_url TEXT,
  description TEXT,
  purchase_links JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- 3. 추천 테이블
CREATE TABLE IF NOT EXISTS recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category VARCHAR(20) NOT NULL,
  image_url TEXT,
  analysis_result JSONB NOT NULL,
  top_products JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 4. 피드백 테이블
CREATE TABLE IF NOT EXISTS feedbacks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id VARCHAR(50) NOT NULL,
  recommendation_id UUID REFERENCES recommendations(id),
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  feedback_scores JSONB NOT NULL,
  comment TEXT,
  processed_data JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 5. 챗봇 세션 테이블
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recommendation_id UUID REFERENCES recommendations(id),
  context JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. 챗봇 메시지 테이블
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  message TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_beauty_profiles_user ON beauty_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_finish ON products(finish);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_user ON feedbacks(user_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_product ON feedbacks(product_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);

-- 업데이트 시간 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_beauty_profiles_updated_at 
BEFORE UPDATE ON beauty_profiles 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at 
BEFORE UPDATE ON chat_sessions 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();