import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import json
from typing import List, Dict

class BeautyLoRATrainer:
    def __init__(self, 
                 base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
                 output_dir: str = "./lora_beauty_model"):
        
        self.base_model = base_model
        self.output_dir = output_dir
        
        print(f"베이스 모델 로딩: {base_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True
        )
        
        self.model = prepare_model_for_kbit_training(self.model)
        
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        self.model = get_peft_model(self.model, lora_config)
        
        print("LoRA 어댑터 적용 완료")
        self.model.print_trainable_parameters()
    
    def create_training_data(self, examples: List[Dict]) -> Dataset:
        formatted_data = []
        
        for example in examples:
            prompt = self._format_training_prompt(example)
            formatted_data.append({"text": prompt})
        
        dataset = Dataset.from_list(formatted_data)
        return dataset
    
    def _format_training_prompt(self, example: Dict) -> str:
        region_korean = {
            'lips': '립',
            'cheeks': '블러셔',
            'eyeshadow': '아이섀도우'
        }[example['region']]
        
        finish_korean = {
            'matte': '매트',
            'glossy': '글로시',
            'shimmer': '시머',
            'glitter': '글리터'
        }[example['detected_finish']]
        
        product_finish_korean = {
            'matte': '매트',
            'glossy': '글로시',
            'shimmer': '시머',
            'glitter': '글리터'
        }[example['product_finish']]
        
        messages = [
            {"role": "system", "content": "당신은 K-뷰티 전문 메이크업 어시스턴트입니다."},
            {"role": "user", "content": f"""당신은 K-뷰티 전문 메이크업 어시스턴트입니다. 사용자의 현재 메이크업과 추천 제품을 비교하여 자연스럽고 친근한 추천 문장을 생성하세요.

### 사용자 정보
- 부위: {region_korean}
- 현재 색상: L={example['detected_L']}, a={example['detected_a']}, b={example['detected_b']}
- 현재 질감: {finish_korean}

### 추천 제품
- 브랜드: {example['brand']}
- 제품명: {example['product_name']}
- 색상명: {example['color_name']}
- 질감: {product_finish_korean}
- 유사도: {example['similarity']}%
- 색차(ΔE): {example['delta_e']}

### 작성 지침
1. 친근하고 자연스러운 어투 (존댓말)
2. 색상 차이를 감각적으로 표현
3. 질감 특징 언급
4. 2-3문장으로 간결하게
5. 기술적 수치 언급 금지

추천 문장:"""},
            {"role": "assistant", "content": example['recommendation_text']}
        ]
        
        formatted_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        
        return formatted_text
    
    def train(self, train_dataset: Dataset, epochs: int = 3, batch_size: int = 4):
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=512,
                padding="max_length"
            )
        
        tokenized_dataset = train_dataset.map(
            tokenize_function,
            remove_columns=train_dataset.column_names
        )
        
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            fp16=True,
            save_strategy="epoch",
            logging_steps=10,
            warmup_steps=50,
            optim="paged_adamw_8bit"
        )
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator
        )
        
        print("학습 시작...")
        trainer.train()
        
        print(f"LoRA 어댑터 저장: {self.output_dir}")
        self.model.save_pretrained(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        
        print("학습 완료")


def create_sample_training_data() -> List[Dict]:
    return [
        {
            'region': 'lips',
            'detected_L': 40, 'detected_a': 55, 'detected_b': 28,
            'detected_finish': 'matte',
            'brand': '3CE',
            'product_name': 'Velvet Lip Tint',
            'color_name': 'Taupe',
            'product_finish': 'matte',
            'similarity': 95.5,
            'delta_e': 4.2,
            'recommendation_text': '3CE의 Velvet Lip Tint Taupe 색상을 추천드려요. 현재 사용하시는 색상과 거의 동일한 톤으로 자연스러운 MLBB 연출이 가능해요. 부드럽고 세련된 매트 마감이 특징이에요.'
        },
        {
            'region': 'lips',
            'detected_L': 38, 'detected_a': 60, 'detected_b': 30,
            'detected_finish': 'matte',
            'brand': 'ETUDE',
            'product_name': 'Dear Darling Water Gel Tint',
            'color_name': 'Cherry Ade',
            'product_finish': 'glossy',
            'similarity': 88.3,
            'delta_e': 8.5,
            'recommendation_text': 'ETUDE의 Dear Darling Water Gel Tint Cherry Ade를 추천드려요. 현재보다 조금 더 밝고 생기있는 컬러로 화사한 인상을 줄 수 있어요. 매트한 질감에서 촉촉하고 윤기나는 글로시 마감으로 변화를 주실 수 있어요.'
        },
        {
            'region': 'cheeks',
            'detected_L': 55, 'detected_a': 42, 'detected_b': 28,
            'detected_finish': 'matte',
            'brand': '3CE',
            'product_name': 'Mood Recipe Face Blush',
            'color_name': 'Mono Pink',
            'product_finish': 'shimmer',
            'similarity': 92.1,
            'delta_e': 5.8,
            'recommendation_text': '3CE의 Mood Recipe Face Blush Mono Pink를 추천드려요. 현재 사용하시는 색상과 비슷한 톤이지만 은은한 펄감이 살아있는 시머 질감으로 입체감을 더해줄 거예요.'
        },
        {
            'region': 'eyeshadow',
            'detected_L': 48, 'detected_a': 28, 'detected_b': 22,
            'detected_finish': 'matte',
            'brand': 'ROM&ND',
            'product_name': 'Better Than Palette',
            'color_name': 'Mahogany Garden',
            'product_finish': 'shimmer',
            'similarity': 89.5,
            'delta_e': 7.2,
            'recommendation_text': 'ROM&ND의 Better Than Palette Mahogany Garden 색상을 추천드려요. 현재보다 살짝 깊이감 있는 컬러로 세련된 분위기를 연출할 수 있어요. 은은한 시머가 눈매를 더욱 도드라지게 해줄 거예요.'
        },
        {
            'region': 'lips',
            'detected_L': 35, 'detected_a': 58, 'detected_b': 25,
            'detected_finish': 'glossy',
            'brand': 'CLIO',
            'product_name': 'Mad Matte Lips',
            'color_name': 'Bloody Sweet',
            'product_finish': 'matte',
            'similarity': 86.7,
            'delta_e': 9.8,
            'recommendation_text': 'CLIO의 Mad Matte Lips Bloody Sweet를 추천드려요. 현재보다 조금 더 선명하고 화사한 컬러로 포인트 메이크업이 가능해요. 글로시한 질감에서 부드럽고 세련된 매트 마감으로 변화를 줘보세요.'
        }
    ]


if __name__ == "__main__":
    print("=== LoRA 파인튜닝 예제 ===\n")
    print("이 스크립트는 실제 학습을 위한 템플릿입니다.")
    print("실행하려면 PyTorch, Transformers, PEFT, bitsandbytes가 필요합니다.\n")
    
    print("샘플 학습 데이터:")
    sample_data = create_sample_training_data()
    for i, example in enumerate(sample_data[:2], 1):
        print(f"\n예제 {i}:")
        print(f"  영역: {example['region']}")
        print(f"  제품: {example['brand']} {example['product_name']}")
        print(f"  추천문: {example['recommendation_text']}")
    
    print("\n\n실제 학습 코드 (주석 처리됨):")
    print("""
# trainer = BeautyLoRATrainer(
#     base_model="meta-llama/Meta-Llama-3-8B-Instruct",
#     output_dir="./lora_beauty_model"
# )
# 
# training_data = create_sample_training_data()
# dataset = trainer.create_training_data(training_data)
# 
# trainer.train(dataset, epochs=3, batch_size=4)
    """)
