-- 기존 beauty_profiles 테이블 삭제하고 재생성
DROP TABLE IF EXISTS beauty_profiles CASCADE;

CREATE TABLE beauty_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- 퍼스널 컬러 (12가지 - 4계절 × 3타입)
  personal_color VARCHAR(30) NOT NULL CHECK (personal_color IN (
    'bright_spring', 'true_spring', 'light_spring',
    'light_summer', 'true_summer', 'soft_summer',
    'soft_autumn', 'true_autumn', 'deep_autumn',
    'deep_winter', 'true_winter', 'bright_winter'
  )),
  
  -- 피부 언더톤
  skin_undertone VARCHAR(20) NOT NULL CHECK (skin_undertone IN ('warm', 'cool', 'neutral')),
  
  -- 피부 타입
  skin_type VARCHAR(20) NOT NULL CHECK (skin_type IN ('oily', 'dry', 'combination', 'sensitive')),
  
  -- 명암 대비
  contrast_level VARCHAR(20) NOT NULL CHECK (contrast_level IN ('high', 'medium', 'low')),
  
  -- 선호 피니시
  preferred_finish VARCHAR(20) NOT NULL CHECK (preferred_finish IN ('matte', 'glossy', 'satin', 'velvet', 'dewy')),
  
  -- 선호 매장
  preferred_store VARCHAR(20) NOT NULL CHECK (preferred_store IN ('roadshop', 'department', 'online', 'luxury')),
  
  -- 가격대 선호 (원 단위)
  price_range_min INTEGER DEFAULT 5000,
  price_range_max INTEGER DEFAULT 50000,
  
  -- 기타 선호사항 (JSON - 확장용)
  preferences JSONB DEFAULT '{}',
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id)
);

-- 인덱스
CREATE INDEX idx_beauty_profiles_user ON beauty_profiles(user_id);
CREATE INDEX idx_beauty_profiles_personal_color ON beauty_profiles(personal_color);
CREATE INDEX idx_beauty_profiles_skin_type ON beauty_profiles(skin_type);
CREATE INDEX idx_beauty_profiles_undertone ON beauty_profiles(skin_undertone);

-- 트리거
CREATE TRIGGER update_beauty_profiles_updated_at 
BEFORE UPDATE ON beauty_profiles 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();