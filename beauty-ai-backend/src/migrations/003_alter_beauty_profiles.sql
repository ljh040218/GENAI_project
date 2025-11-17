-- DROP TABLE 대신 ALTER TABLE 사용

-- 선택 필드를 nullable로 변경
ALTER TABLE beauty_profiles 
  ALTER COLUMN skin_type DROP NOT NULL;

ALTER TABLE beauty_profiles 
  ALTER COLUMN contrast_level DROP NOT NULL;

ALTER TABLE beauty_profiles 
  ALTER COLUMN preferred_finish DROP NOT NULL;

ALTER TABLE beauty_profiles 
  ALTER COLUMN preferred_store DROP NOT NULL;

-- 가격 범위 기본값 제거
ALTER TABLE beauty_profiles 
  ALTER COLUMN price_range_min DROP DEFAULT;

ALTER TABLE beauty_profiles 
  ALTER COLUMN price_range_max DROP DEFAULT;

-- 확인
SELECT 
  column_name, 
  data_type, 
  is_nullable, 
  column_default
FROM information_schema.columns
WHERE table_name = 'beauty_profiles'
ORDER BY ordinal_position;