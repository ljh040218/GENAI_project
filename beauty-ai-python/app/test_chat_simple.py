import requests
import json

BASE_URL = "https://pythonapi-production-8efe.up.railway.app"
USER_ID = "test_user_001"

def chat_with_agent(message: str, category: str = "lips"):
    """RAG Agent와 대화"""
    payload = {
        "user_id": USER_ID,
        "message": message,
        "current_recommendations": [],
        "user_profile": {
            "tone": "cool",
            "fav_brands": ["롬앤", "3CE"],
            "finish_preference": ["glossy", "satin"],
            "price_range": [10000, 30000]
        },
        "category": category
    }
    
    response = requests.post(f"{BASE_URL}/api/agent/message", json=payload)
    result = response.json()
    
    print("\n" + "="*60)
    print(f"🙋 사용자: {message}")
    print("="*60)
    
    if result.get("success"):
        print(f"\n🤖 AI: {result.get('assistant_message', '')}")
        
        if result.get("intent"):
            print(f"\n📊 Intent: {result['intent']}")
        
        if result.get("text_based_recommendations"):
            print("\n📦 추천 제품 (사용자 피드백 기반):")
            for i, prod in enumerate(result["text_based_recommendations"][:3], 1):
                print(f"  {i}. {prod.get('brand')} - {prod.get('product_name')} ({prod.get('shade_name')})")
                print(f"     Finish: {prod.get('finish')}, Price: {prod.get('price')}원")
        
        if result.get("profile_based_recommendations"):
            print("\n📦 추천 제품 (프로필 기반):")
            for i, prod in enumerate(result["profile_based_recommendations"][:3], 1):
                print(f"  {i}. {prod.get('brand')} - {prod.get('product_name')} ({prod.get('shade_name')})")
                print(f"     Finish: {prod.get('finish')}, Price: {prod.get('price')}원")
    else:
        print(f"❌ 에러: {result.get('detail', 'Unknown error')}")
    
    print("="*60)


def check_memory():
    """메모리 확인"""
    response = requests.get(f"{BASE_URL}/api/memory/stats/{USER_ID}")
    result = response.json()
    
    print("\n" + "="*60)
    print("💾 메모리 통계")
    print("="*60)
    print(f"총 피드백 수: {result.get('total_feedbacks', 0)}")
    print(f"\nIntent 분포:")
    for intent, count in result.get('intent_distribution', {}).items():
        print(f"  - {intent}: {count}개")
    
    if result.get('recent_feedbacks'):
        print(f"\n최근 피드백:")
        for fb in result['recent_feedbacks']:
            print(f"  - {fb['text']}")
    print("="*60)


def main():
    print("\n🎨 K-Beauty AI RAG Agent 테스트")
    print("="*60)
    
    # 테스트 시나리오
    scenarios = [
        "MLBB 립스틱 추천해줘",
        "좀 더 매트한 느낌으로",
        "이 제품이 왜 나한테 맞아?",
        "요즘 유행하는 립 색상 알려줘",
        "쿨톤에 어울리는 블러셔 추천"
    ]
    
    for message in scenarios:
        chat_with_agent(message)
        input("\n계속하려면 Enter를 누르세요...")
    
    # 메모리 확인
    check_memory()


if __name__ == "__main__":
    main()
