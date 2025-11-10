#!/bin/bash

echo "=================================="
echo "Beauty AI Backend Setup Script"
echo "=================================="
echo ""

if ! command -v node &> /dev/null; then
    echo "Node.js가 설치되어 있지 않습니다."
    echo "Node.js를 먼저 설치해주세요: https://nodejs.org/"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "PostgreSQL이 설치되어 있지 않습니다."
    echo "PostgreSQL을 먼저 설치해주세요."
    exit 1
fi

echo "1. 의존성 패키지 설치 중..."
npm install

if [ ! -f .env ]; then
    echo ""
    echo "2. 환경 변수 파일 생성 중..."
    cp .env.example .env
    echo ".env 파일이 생성되었습니다. 데이터베이스 설정을 확인해주세요."
else
    echo ""
    echo "2. .env 파일이 이미 존재합니다."
fi

echo ""
echo "=================================="
echo "설치 완료!"
echo "=================================="
echo ""
echo "다음 단계:"
echo "1. PostgreSQL에서 데이터베이스 생성:"
echo "   createdb beauty_ai_db"
echo ""
echo "2. 스키마 적용:"
echo "   psql -U postgres -d beauty_ai_db -f database/schema.sql"
echo ""
echo "3. .env 파일 수정 (데이터베이스 비밀번호 등)"
echo ""
echo "4. 서버 실행:"
echo "   npm run dev"
echo ""
