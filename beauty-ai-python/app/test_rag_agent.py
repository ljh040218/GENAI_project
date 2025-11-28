import requests
import json
from typing import Dict, List

BASE_URL = "https://beauty-ai-python-production.up.railway.app"

class RAGAgentTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.user_id = "test_user_001"
    
    def test_health(self):
        """1. Health Check"""
        print("\n" + "="*60)
        print("TEST 1: Health Check")
        print("="*60)
        
        response = requests.get(f"{self.base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    
    def test_agent_recommend(self):
        """2. 제품 추천 요청"""
        print("\n" + "="*60)
        print("TEST 2: 제품 추천 요청")
        print("="*60)
        
        payload = {
            "user_id": self.user_id,
            "message": "MLBB 립스틱 추천해줘",
            "current_recommendations": [],
            "user_profile": {
                "tone": "cool",
                "fav_brands": ["롬앤", "3CE"],
                "finish_preference": ["glossy", "satin"],
                "price_range": [10000, 30000]
            },
            "category": "lips"
        }
        
        print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{self.base_url}/api/agent/message",
            json=payload
        )
        
        print(f"\nStatus: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
    
    def test_agent_re_recommend(self):
        """3. 재추천 요청 (피드백 포함)"""
        print("\n" + "="*60)
        print("TEST 3: 재추천 요청 (피드백)")
        print("="*60)
        
        current_recs = [
            {
                "brand": "롬앤",
                "product_name": "쥬시 래스팅 틴트",
                "shade_name": "핑크 베리",
                "finish": "glossy",
                "price": 8900
            }
        ]
        
        payload = {
            "user_id": self.user_id,
            "message": "좀 더 매트한 느낌으로 바꿔줘",
            "current_recommendations": current_recs,
            "user_profile": {
                "tone": "cool",
                "fav_brands": ["롬앤", "3CE"],
                "finish_preference": ["glossy"],
                "price_range": [10000, 30000]
            },
            "category": "lips"
        }
        
        print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{self.base_url}/api/agent/message",
            json=payload
        )
        
        print(f"\nStatus: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
    
    def test_agent_explain(self):
        """4. 제품 설명 요청"""
        print("\n" + "="*60)
        print("TEST 4: 제품 설명 요청")
        print("="*60)
        
        current_recs = [
            {
                "brand": "롬앤",
                "product_name": "쥬시 래스팅 틴트",
                "shade_name": "핑크 베리",
                "finish": "glossy"
            }
        ]
        
        payload = {
            "user_id": self.user_id,
            "message": "이 제품 왜 추천된 거야?",
            "current_recommendations": current_recs,
            "user_profile": {
                "tone": "cool"
            },
            "category": "lips"
        }
        
        print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{self.base_url}/api/agent/message",
            json=payload
        )
        
        print(f"\nStatus: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
    
    def test_agent_trend(self):
        """5. 트렌드 질문"""
        print("\n" + "="*60)
        print("TEST 5: 트렌드 질문")
        print("="*60)
        
        payload = {
            "user_id": self.user_id,
            "message": "요즘 유행하는 립 색상이 뭐야?",
            "current_recommendations": [],
            "user_profile": {},
            "category": "lips"
        }
        
        print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{self.base_url}/api/agent/message",
            json=payload
        )
        
        print(f"\nStatus: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
    
    def test_memory_stats(self):
        """6. 메모리 통계 확인"""
        print("\n" + "="*60)
        print("TEST 6: 메모리 통계 확인")
        print("="*60)
        
        response = requests.get(
            f"{self.base_url}/api/memory/stats/{self.user_id}"
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
    
    def test_memory_search(self):
        """7. 과거 피드백 검색"""
        print("\n" + "="*60)
        print("TEST 7: 과거 피드백 검색")
        print("="*60)
        
        payload = {
            "user_id": self.user_id,
            "query": "MLBB 립스틱",
            "top_k": 5
        }
        
        print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{self.base_url}/api/memory/search",
            json=payload
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "🚀 " + "="*58)
        print("🚀 RAG Agent 챗봇 테스트 시작")
        print("🚀 " + "="*58)
        
        try:
            # 1. Health Check
            self.test_health()
            
            # 2. 추천 요청
            self.test_agent_recommend()
            
            # 3. 재추천
            self.test_agent_re_recommend()
            
            # 4. 설명 요청
            self.test_agent_explain()
            
            # 5. 트렌드 질문
            self.test_agent_trend()
            
            # 6. 메모리 통계
            self.test_memory_stats()
            
            # 7. 메모리 검색
            self.test_memory_search()
            
            print("\n" + "✨ " + "="*58)
            print("✨ 모든 테스트 완료!")
            print("✨ " + "="*58)
            
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")


def main():
    tester = RAGAgentTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
