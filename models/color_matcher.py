import numpy as np
from sklearn.neighbors import NearestNeighbors
from typing import Dict, List, Tuple, Optional

FINISH_TYPES = {
    'matte': 0,
    'shimmer': 1,
    'glitter': 2,
    'glossy': 3,
    'unknown': 4
}

REGION_FINISH_MAP = {
    'lips': ['matte', 'shimmer', 'glitter', 'glossy'],
    'cheeks': ['matte', 'shimmer', 'glitter'],
    'eyeshadow': ['matte', 'shimmer', 'glitter']
}

class ProductMatcher:
    def __init__(self, color_weight=0.7, finish_weight=0.3):
        self.color_weight = color_weight
        self.finish_weight = finish_weight
        self.knn_models = {}
        self.products_db = {}
        
    def _encode_finish(self, finish: str) -> int:
        finish_lower = finish.lower() if finish else 'unknown'
        return FINISH_TYPES.get(finish_lower, FINISH_TYPES['unknown'])
    
    def _validate_finish_for_region(self, region: str, finish: str) -> bool:
        finish_lower = finish.lower() if finish else 'unknown'
        if finish_lower == 'unknown':
            return True
        return finish_lower in REGION_FINISH_MAP.get(region, [])
    
    def load_products(self, products: List[Dict], region: str):
        valid_products = []
        features = []
        
        for product in products:
            finish = product.get('finish', 'unknown')
            
            if not self._validate_finish_for_region(region, finish):
                continue
            
            L = product['color']['L']
            a = product['color']['a']
            b = product['color']['b']
            
            if region == 'cheeks':
                feature = [L, a, b]
            else:
                finish_code = self._encode_finish(finish)
                feature = [L, a, b, finish_code]
            
            features.append(feature)
            valid_products.append(product)
        
        if not features:
            raise ValueError(f"No valid products for region: {region}")
        
        features_array = np.array(features)
        
        knn = NearestNeighbors(n_neighbors=min(10, len(features)), metric='euclidean')
        knn.fit(features_array)
        
        self.knn_models[region] = knn
        self.products_db[region] = {
            'products': valid_products,
            'features': features_array
        }
    
    def find_matches(self, region: str, target_color: Dict, target_finish: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        if region not in self.knn_models:
            raise ValueError(f"No products loaded for region: {region}")
        
        knn = self.knn_models[region]
        db = self.products_db[region]
        
        L = target_color['L']
        a = target_color['a']
        b = target_color['b']
        
        if region == 'cheeks':
            query = np.array([[L, a, b]])
        else:
            finish_code = self._encode_finish(target_finish or 'unknown')
            query = np.array([[L, a, b, finish_code]])
        
        distances, indices = knn.kneighbors(query)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            product = db['products'][idx].copy()
            
            prod_L = product['color']['L']
            prod_a = product['color']['a']
            prod_b = product['color']['b']
            
            delta_e = np.sqrt((L - prod_L)**2 + (a - prod_a)**2 + (b - prod_b)**2)
            
            color_similarity = max(0, 100 - delta_e * 2)
            
            if region == 'cheeks':
                finish_match = 1.0
            else:
                if target_finish and product.get('finish'):
                    finish_match = 1.0 if target_finish.lower() == product['finish'].lower() else 0.3
                else:
                    finish_match = 0.5
            
            similarity_score = (
                self.color_weight * color_similarity +
                self.finish_weight * finish_match * 100
            )
            
            product['similarity_score'] = round(similarity_score, 2)
            product['delta_e'] = round(delta_e, 2)
            product['knn_distance'] = round(float(dist), 2)
            
            results.append(product)
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]
    
    def get_recommendation_reason(self, target_color: Dict, product: Dict, target_finish: Optional[str] = None) -> str:
        delta_e = product['delta_e']
        
        if delta_e < 5:
            color_desc = "색상이 매우 유사"
        elif delta_e < 10:
            color_desc = "색상이 유사"
        elif delta_e < 20:
            color_desc = "색상이 비슷한 편"
        else:
            color_desc = "색상에 차이가 있음"
        
        reason = color_desc
        
        if target_finish and product.get('finish'):
            if target_finish.lower() == product['finish'].lower():
                reason += f", {product['finish']} 질감 일치"
        
        return reason


if __name__ == "__main__":
    sample_lip_products = [
        {
            'brand': 'MAC',
            'product_name': 'Retro Matte',
            'color_name': 'Ruby Woo',
            'color': {'L': 40, 'a': 60, 'b': 30},
            'finish': 'matte'
        },
        {
            'brand': 'Dior',
            'product_name': 'Addict Lip Glow',
            'color_name': 'Pink',
            'color': {'L': 50, 'a': 40, 'b': 20},
            'finish': 'glossy'
        },
        {
            'brand': 'YSL',
            'product_name': 'Rouge Volupté Shine',
            'color_name': 'Rose Burgundy',
            'color': {'L': 35, 'a': 55, 'b': 25},
            'finish': 'glossy'
        },
        {
            'brand': 'NARS',
            'product_name': 'Powermatte',
            'color_name': 'Starwoman',
            'color': {'L': 42, 'a': 58, 'b': 28},
            'finish': 'matte'
        },
        {
            'brand': 'Fenty Beauty',
            'product_name': 'Gloss Bomb',
            'color_name': 'Diamond Milk',
            'color': {'L': 55, 'a': 15, 'b': 10},
            'finish': 'glitter'
        }
    ]
    
    sample_cheek_products = [
        {
            'brand': 'NARS',
            'product_name': 'Blush',
            'color_name': 'Orgasm',
            'color': {'L': 55, 'a': 45, 'b': 30},
            'finish': 'shimmer'
        },
        {
            'brand': 'Benefit',
            'product_name': 'Benetint',
            'color_name': 'Rose',
            'color': {'L': 50, 'a': 50, 'b': 25},
            'finish': 'matte'
        },
        {
            'brand': '3CE',
            'product_name': 'Mood Recipe Blush',
            'color_name': 'Cabbage Rose',
            'color': {'L': 52, 'a': 48, 'b': 28},
            'finish': 'matte'
        }
    ]
    
    sample_eyeshadow_products = [
        {
            'brand': 'Urban Decay',
            'product_name': 'Naked Palette',
            'color_name': 'Smog',
            'color': {'L': 45, 'a': 10, 'b': 25},
            'finish': 'shimmer'
        },
        {
            'brand': 'Anastasia',
            'product_name': 'Modern Renaissance',
            'color_name': 'Burnt Orange',
            'color': {'L': 50, 'a': 30, 'b': 35},
            'finish': 'matte'
        },
        {
            'brand': 'Stila',
            'product_name': 'Glitter & Glow',
            'color_name': 'Kitten Karma',
            'color': {'L': 60, 'a': 5, 'b': 20},
            'finish': 'glitter'
        }
    ]
    
    print("=== KNN 기반 제품 매칭 테스트 ===\n")
    
    matcher = ProductMatcher(color_weight=0.7, finish_weight=0.3)
    
    print("1. 립 제품 로드 (glossy 포함)")
    matcher.load_products(sample_lip_products, 'lips')
    print(f"   로드된 제품 수: {len(matcher.products_db['lips']['products'])}\n")
    
    print("2. 치크 제품 로드 (질감 고려 안함)")
    matcher.load_products(sample_cheek_products, 'cheeks')
    print(f"   로드된 제품 수: {len(matcher.products_db['cheeks']['products'])}\n")
    
    print("3. 아이섀도우 제품 로드 (glossy 제외)")
    matcher.load_products(sample_eyeshadow_products, 'eyeshadow')
    print(f"   로드된 제품 수: {len(matcher.products_db['eyeshadow']['products'])}\n")
    
    test_cases = {
        'lips': {
            'color': {'L': 38, 'a': 62, 'b': 32},
            'finish': 'glossy'
        },
        'cheeks': {
            'color': {'L': 53, 'a': 47, 'b': 29},
            'finish': None
        },
        'eyeshadow': {
            'color': {'L': 48, 'a': 12, 'b': 28},
            'finish': 'shimmer'
        }
    }
    
    for region, test_data in test_cases.items():
        print(f"\n{'='*60}")
        print(f"[{region.upper()}] 매칭 결과")
        print(f"{'='*60}")
        print(f"타겟 색상: L={test_data['color']['L']}, a={test_data['color']['a']}, b={test_data['color']['b']}")
        if test_data['finish']:
            print(f"타겟 질감: {test_data['finish']}")
        else:
            print("타겟 질감: 고려 안함 (블러셔)")
        
        products = matcher.find_matches(
            region=region,
            target_color=test_data['color'],
            target_finish=test_data['finish'],
            top_k=3
        )
        
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['brand']} - {product['product_name']}")
            print(f"   색상: {product['color_name']}")
            print(f"   피니시: {product['finish']}")
            print(f"   유사도: {product['similarity_score']}%")
            print(f"   색차(ΔE): {product['delta_e']}")
            print(f"   KNN 거리: {product['knn_distance']}")
            
            reason = matcher.get_recommendation_reason(
                test_data['color'],
                product,
                test_data['finish']
            )
            print(f"   추천 이유: {reason}")
    
    print("\n=== 테스트 완료 ===")