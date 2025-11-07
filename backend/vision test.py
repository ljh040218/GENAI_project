import cv2
import numpy as np
from typing import Dict, List
from color_utils import region_mean_lab_spatial, deltaE

class MakeupRecommendationPipeline:
    def __init__(self, 
                 vision_encoder_model_path=None,
                 color_weight=0.7,
                 finish_weight=0.3):
        
        from face_parser import MPFaceParser
        from vision_encoder import CNNVisionEncoder
        from product_matcher import ProductMatcher
        
        self.face_parser = MPFaceParser()
        self.vision_encoder = CNNVisionEncoder(model_path=vision_encoder_model_path)
        self.product_matcher = ProductMatcher(
            color_weight=color_weight,
            finish_weight=finish_weight
        )
        
        self.products_loaded = False
    
    def load_product_database(self, products_by_region: Dict[str, List[Dict]]):
        for region, products in products_by_region.items():
            if region in ['lips', 'cheeks', 'eyeshadow']:
                self.product_matcher.load_products(products, region)
        
        self.products_loaded = True
        print("✅ 제품 데이터베이스 로드 완료")
    
    def _extract_color_from_mask(self, image_bgr: np.ndarray, mask: np.ndarray, region: str) -> Dict:
        if region == 'lips':
            lab = region_mean_lab_spatial(image_bgr, mask, center_weight=0.8)
        elif region == 'cheeks':
            lab = region_mean_lab_spatial(image_bgr, mask, center_weight=0.6)
        elif region == 'eyeshadow':
            lab = region_mean_lab_spatial(image_bgr, mask, center_weight=0.7)
        else:
            lab = region_mean_lab_spatial(image_bgr, mask, center_weight=0.7)
        
        return {
            'L': round(lab[0], 2),
            'a': round(lab[1], 2),
            'b': round(lab[2], 2)
        }
    
    def analyze_face(self, image_path: str, top_k: int = 5) -> Dict:
        if not self.products_loaded:
            raise ValueError("제품 데이터베이스를 먼저 로드하세요 (load_product_database)")
        
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            raise ValueError(f"이미지를 불러올 수 없습니다: {image_path}")
        
        print("1. 얼굴 영역 파싱 중...")
        masks = self.face_parser.parse(image_bgr)
        
        print("2. 색상 추출 중...")
        colors = {}
        for region in ['lips', 'cheeks', 'eyeshadow']:
            colors[region] = self._extract_color_from_mask(image_bgr, masks[region], region)
        
        print("3. 피니시 분류 중...")
        finishes = self.vision_encoder.predict_all_regions(image_bgr, masks)
        
        print("4. 제품 매칭 중...")
        recommendations = {}
        
        for region in ['lips', 'cheeks', 'eyeshadow']:
            target_finish = finishes[region]['finish'] if finishes[region]['finish'] != 'unknown' else None
            
            if region == 'cheeks':
                target_finish = None
            
            matched_products = self.product_matcher.find_matches(
                region=region,
                target_color=colors[region],
                target_finish=target_finish,
                top_k=top_k
            )
            
            recommendations[region] = {
                'detected_color': colors[region],
                'detected_finish': finishes[region],
                'recommended_products': matched_products
            }
        
        return recommendations
    
    def print_results(self, results: Dict):
        print("\n" + "="*80)
        print("메이크업 제품 추천 결과")
        print("="*80)
        
        for region, data in results.items():
            print(f"\n[{region.upper()}]")
            print(f"  감지된 색상: L={data['detected_color']['L']}, "
                  f"a={data['detected_color']['a']}, b={data['detected_color']['b']}")
            
            finish_info = data['detected_finish']
            print(f"  감지된 피니시: {finish_info['finish']} "
                  f"(신뢰도: {finish_info['confidence']}, 방법: {finish_info['method']})")
            
            print(f"\n  추천 제품 TOP {len(data['recommended_products'])}:")
            for i, product in enumerate(data['recommended_products'], 1):
                print(f"\n  {i}. {product['brand']} - {product['product_name']}")
                print(f"     색상: {product['color_name']}")
                print(f"     피니시: {product['finish']}")
                print(f"     유사도: {product['similarity_score']}%")
                print(f"     색차(ΔE): {product['delta_e']}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    sample_products = {
        'lips': [
            {
                'brand': '3CE',
                'product_name': 'Velvet Lip Tint',
                'color_name': 'Taupe',
                'color': {'L': 42, 'a': 25, 'b': 18},
                'finish': 'matte'
            },
            {
                'brand': 'ETUDE',
                'product_name': 'Dear Darling Water Gel Tint',
                'color_name': 'Cherry Ade',
                'color': {'L': 38, 'a': 58, 'b': 28},
                'finish': 'glossy'
            },
            {
                'brand': 'PERIPERA',
                'product_name': 'Ink Velvet',
                'color_name': 'Celeb Deep Rose',
                'color': {'L': 35, 'a': 52, 'b': 22},
                'finish': 'matte'
            },
            {
                'brand': 'ROM&ND',
                'product_name': 'Juicy Lasting Tint',
                'color_name': 'Figfig',
                'color': {'L': 40, 'a': 48, 'b': 25},
                'finish': 'glossy'
            },
            {
                'brand': 'CLIO',
                'product_name': 'Mad Matte Lips',
                'color_name': 'Bloody Sweet',
                'color': {'L': 36, 'a': 60, 'b': 30},
                'finish': 'matte'
            },
        ],
        'cheeks': [
            {
                'brand': 'ETUDE',
                'product_name': 'Lovely Cookie Blusher',
                'color_name': 'Grapefruit Jelly',
                'color': {'L': 55, 'a': 42, 'b': 28},
                'finish': 'matte'
            },
            {
                'brand': '3CE',
                'product_name': 'Mood Recipe Face Blush',
                'color_name': 'Mono Pink',
                'color': {'L': 52, 'a': 48, 'b': 26},
                'finish': 'shimmer'
            },
            {
                'brand': 'PERIPERA',
                'product_name': 'Pure Blushed Liquid Cheek',
                'color_name': 'Healthy Pink',
                'color': {'L': 50, 'a': 45, 'b': 24},
                'finish': 'matte'
            },
            {
                'brand': 'CLIO',
                'product_name': 'Prism Air Blusher',
                'color_name': 'Coral Lychee',
                'color': {'L': 54, 'a': 40, 'b': 30},
                'finish': 'shimmer'
            },
        ],
        'eyeshadow': [
            {
                'brand': 'ETUDE',
                'product_name': 'Play Color Eyes',
                'color_name': 'Rose Bomb',
                'color': {'L': 48, 'a': 28, 'b': 22},
                'finish': 'shimmer'
            },
            {
                'brand': 'ROM&ND',
                'product_name': 'Better Than Palette',
                'color_name': 'Mahogany Garden',
                'color': {'L': 45, 'a': 32, 'b': 28},
                'finish': 'matte'
            },
            {
                'brand': 'CLIO',
                'product_name': 'Pro Eye Palette',
                'color_name': 'Simply Pink',
                'color': {'L': 52, 'a': 22, 'b': 18},
                'finish': 'shimmer'
            },
            {
                'brand': '3CE',
                'product_name': 'Multi Eye Color Palette',
                'color_name': 'Nude Beige',
                'color': {'L': 50, 'a': 15, 'b': 25},
                'finish': 'matte'
            },
            {
                'brand': 'PERIPERA',
                'product_name': 'Ink Glitter',
                'color_name': 'Rose Gold',
                'color': {'L': 55, 'a': 18, 'b': 20},
                'finish': 'glitter'
            },
        ]
    }
    
    print("=== 메이크업 추천 파이프라인 테스트 ===\n")
    
    pipeline = MakeupRecommendationPipeline()
    
    pipeline.load_product_database(sample_products)
    
    print("\n사용법:")
    print("  results = pipeline.analyze_face('your_face_image.jpg')")
    print("  pipeline.print_results(results)")
    print("\n참고: 실제 얼굴 이미지가 필요합니다.")