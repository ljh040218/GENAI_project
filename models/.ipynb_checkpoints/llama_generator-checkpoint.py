try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch/Transformers 미설치. 규칙 기반 모드로 실행됩니다.")

from typing import Dict, List, Optional
import json

class BeautyRecommendationGenerator:
    def __init__(self, 
                 model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct",
                 lora_path: Optional[str] = None,
                 device: Optional[str] = None):
        
        if not TORCH_AVAILABLE:
            print("PyTorch 미설치. 규칙 기반 모드로 실행됩니다.")
            self.model = None
            self.tokenizer = None
            self.device = None
            return
        
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"디바이스: {self.device}")
        
        try:
            print(f"모델 로딩 중: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device.type == 'cuda' else torch.float32,
                device_map='auto' if self.device.type == 'cuda' else None,
                low_cpu_mem_usage=True
            )
            
            if lora_path:
                print(f"LoRA 어댑터 로딩 중: {lora_path}")
                from peft import PeftModel
                self.model = PeftModel.from_pretrained(self.model, lora_path)
                print("LoRA 어댑터 로드 완료")
            
            if self.device.type != 'cuda':
                self.model = self.model.to(self.device)
            
            self.model.eval()
            print("모델 로드 완료")
            
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            print("규칙 기반 폴백 모드로 전환합니다.")
            self.model = None
            self.tokenizer = None
    
    def _build_prompt(self, 
                     region: str,
                     detected_color: Dict,
                     detected_finish: str,
                     recommended_product: Dict) -> str:
        
        prompt = f"""당신은 K-뷰티 전문 메이크업 어시스턴트입니다. 사용자의 현재 메이크업과 추천 제품을 비교하여 자연스럽고 친근한 추천 문장을 생성하세요.

### 사용자 정보
- 부위: {self._get_region_korean(region)}
- 현재 색상: L={detected_color['L']}, a={detected_color['a']}, b={detected_color['b']}
- 현재 질감: {self._get_finish_korean(detected_finish)}

### 추천 제품
- 브랜드: {recommended_product['brand']}
- 제품명: {recommended_product['product_name']}
- 색상명: {recommended_product['color_name']}
- 질감: {self._get_finish_korean(recommended_product['finish'])}
- 유사도: {recommended_product['similarity_score']}%
- 색차(ΔE): {recommended_product['delta_e']}

### 작성 지침
1. 친근하고 자연스러운 어투 (존댓말)
2. 색상 차이를 감각적으로 표현 (예: "조금 더 밝고 생기있는", "은은하게 발색되는")
3. 질감 특징 언급 (매트/글로시/시머/글리터)
4. 2-3문장으로 간결하게
5. 기술적 수치(L, a, b, ΔE) 언급 금지

추천 문장:"""
        
        return prompt
    
    def _get_region_korean(self, region: str) -> str:
        mapping = {
            'lips': '립',
            'cheeks': '블러셔',
            'eyeshadow': '아이섀도우'
        }
        return mapping.get(region, region)
    
    def _get_finish_korean(self, finish: str) -> str:
        mapping = {
            'matte': '매트',
            'glossy': '글로시',
            'shimmer': '시머',
            'glitter': '글리터',
            'unknown': '알 수 없음'
        }
        return mapping.get(finish.lower(), finish)
    
    def _rule_based_recommendation(self,
                                   region: str,
                                   detected_color: Dict,
                                   detected_finish: str,
                                   recommended_product: Dict) -> str:
        
        delta_e = recommended_product['delta_e']
        similarity = recommended_product['similarity_score']
        
        color_diff = ""
        if delta_e < 5:
            color_diff = "현재 사용하시는 색상과 거의 동일한 톤이에요"
        elif delta_e < 10:
            color_diff = "현재보다 살짝 다른 느낌의 색상이에요"
        elif delta_e < 20:
            if detected_color['L'] < recommended_product['color']['L']:
                color_diff = "현재보다 조금 더 밝고 생기있는 컬러예요"
            else:
                color_diff = "현재보다 조금 더 깊이감 있는 컬러예요"
        else:
            if detected_color['a'] < recommended_product['color']['a']:
                color_diff = "현재보다 훨씬 선명하고 화사한 컬러예요"
            else:
                color_diff = "현재보다 은은하게 발색되는 컬러예요"
        
        finish_text = ""
        if detected_finish != 'unknown' and detected_finish != recommended_product['finish']:
            current = self._get_finish_korean(detected_finish)
            new = self._get_finish_korean(recommended_product['finish'])
            finish_text = f" {current}한 질감에서 {new}한 질감으로 변화를 주실 수 있어요."
        elif recommended_product['finish'] == 'glossy':
            finish_text = " 촉촉하고 윤기나는 글로시 마감이 매력적이에요."
        elif recommended_product['finish'] == 'matte':
            finish_text = " 부드럽고 세련된 매트 마감이 특징이에요."
        elif recommended_product['finish'] == 'shimmer':
            finish_text = " 은은한 �펄감이 살아있는 시머 질감이에요."
        elif recommended_product['finish'] == 'glitter':
            finish_text = " 화려한 글리터가 포인트가 되어줄 거예요."
        
        region_korean = self._get_region_korean(region)
        
        recommendation = f"{recommended_product['brand']}의 {recommended_product['product_name']} {recommended_product['color_name']} 색상을 추천드려요. {color_diff}.{finish_text}"
        
        return recommendation
    
    def generate_recommendation(self,
                               region: str,
                               detected_color: Dict,
                               detected_finish: str,
                               recommended_product: Dict,
                               max_length: int = 150) -> str:
        
        if self.model is None or self.tokenizer is None:
            return self._rule_based_recommendation(
                region, detected_color, detected_finish, recommended_product
            )
        
        try:
            prompt = self._build_prompt(region, detected_color, detected_finish, recommended_product)
            
            messages = [
                {"role": "system", "content": "당신은 K-뷰티 전문 메이크업 어시스턴트입니다."},
                {"role": "user", "content": prompt}
            ]
            
            input_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            inputs = self.tokenizer(input_text, return_tensors="pt")
            if self.device:
                inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if "추천 문장:" in generated_text:
                recommendation = generated_text.split("추천 문장:")[-1].strip()
            else:
                recommendation = generated_text.split("\n")[-1].strip()
            
            return recommendation
            
        except Exception as e:
            print(f"LLM 생성 실패: {e}, 규칙 기반 폴백 사용")
            return self._rule_based_recommendation(
                region, detected_color, detected_finish, recommended_product
            )
    
    def generate_batch_recommendations(self,
                                      recommendations: Dict[str, Dict]) -> Dict[str, List[str]]:
        
        results = {}
        
        for region, data in recommendations.items():
            region_results = []
            
            detected_color = data['detected_color']
            detected_finish = data['detected_finish']['finish']
            
            for product in data['recommended_products']:
                rec_text = self.generate_recommendation(
                    region=region,
                    detected_color=detected_color,
                    detected_finish=detected_finish,
                    recommended_product=product
                )
                region_results.append(rec_text)
            
            results[region] = region_results
        
        return results


if __name__ == "__main__":
    print("=== 뷰티 추천 텍스트 생성기 테스트 ===\n")
    
    generator = BeautyRecommendationGenerator()
    
    sample_recommendation = {
        'region': 'lips',
        'detected_color': {'L': 40, 'a': 55, 'b': 28},
        'detected_finish': 'matte',
        'recommended_product': {
            'brand': '3CE',
            'product_name': 'Velvet Lip Tint',
            'color_name': 'Taupe',
            'color': {'L': 42, 'a': 52, 'b': 26},
            'finish': 'matte',
            'similarity_score': 95.5,
            'delta_e': 4.2
        }
    }
    
    print("추천 문장 생성 중...\n")
    
    recommendation_text = generator.generate_recommendation(
        region=sample_recommendation['region'],
        detected_color=sample_recommendation['detected_color'],
        detected_finish=sample_recommendation['detected_finish'],
        recommended_product=sample_recommendation['recommended_product']
    )
    
    print(f"[립 제품 추천]")
    print(f"제품: {sample_recommendation['recommended_product']['brand']} "
          f"{sample_recommendation['recommended_product']['product_name']} "
          f"{sample_recommendation['recommended_product']['color_name']}")
    print(f"\n추천 문장:\n{recommendation_text}\n")
    
    print("\n=== 테스트 완료 ===")