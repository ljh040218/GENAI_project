import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np
from PIL import Image
import cv2
from typing import Dict, Optional, Tuple

FINISH_CLASSES = ['matte', 'shimmer', 'glitter', 'glossy', 'unknown']
FINISH_TO_IDX = {name: idx for idx, name in enumerate(FINISH_CLASSES)}
IDX_TO_FINISH = {idx: name for idx, name in enumerate(FINISH_CLASSES)}

class CNNVisionEncoder:
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.model = self._build_model()
        self.model.to(self.device)
        
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.eval()
                self.use_cnn = True
                print(f"✅ 파인튜닝 모델 로드 완료: {model_path}")
            except Exception as e:
                print(f"⚠️  모델 로드 실패, 규칙 기반 폴백 사용: {e}")
                self.use_cnn = False
        else:
            print("⚠️  파인튜닝 모델 없음, 규칙 기반 폴백 사용")
            self.use_cnn = False
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def _build_model(self) -> nn.Module:
        model = models.resnet18(pretrained=True)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, len(FINISH_CLASSES))
        return model
    
    def _rule_based_fallback(self, masked_region: np.ndarray, region: str) -> Tuple[str, float]:
        if masked_region is None or masked_region.size == 0:
            return 'unknown', 0.5
        
        mask = np.any(masked_region > 0, axis=2)
        if not np.any(mask):
            return 'unknown', 0.5
        
        region_pixels = masked_region[mask]
        
        hsv = cv2.cvtColor(masked_region, cv2.COLOR_BGR2HSV)
        hsv_pixels = hsv[mask]
        
        v_mean = np.mean(hsv_pixels[:, 2])
        s_mean = np.mean(hsv_pixels[:, 1])
        
        v_std = np.std(hsv_pixels[:, 2])
        
        gray = cv2.cvtColor(masked_region, cv2.COLOR_BGR2GRAY)
        gray_pixels = gray[mask]
        gray_std = np.std(gray_pixels)
        
        if region == 'lips':
            if v_mean > 180 and v_std > 40:
                return 'glossy', 0.7
            elif gray_std > 25 and s_mean > 100:
                return 'glitter', 0.65
            elif v_std > 30:
                return 'shimmer', 0.6
            else:
                return 'matte', 0.6
        
        elif region == 'cheeks':
            if gray_std > 20:
                return 'shimmer', 0.6
            else:
                return 'matte', 0.6
        
        elif region == 'eyeshadow':
            if gray_std > 30:
                return 'glitter', 0.65
            elif gray_std > 20:
                return 'shimmer', 0.6
            else:
                return 'matte', 0.6
        
        return 'unknown', 0.5
    
    def _preprocess_masked_region(self, image_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
        mask_3ch = cv2.merge([mask, mask, mask])
        masked_region = cv2.bitwise_and(image_bgr, mask_3ch)
        
        ys, xs = np.where(mask > 0)
        if len(ys) == 0:
            return np.zeros((224, 224, 3), dtype=np.uint8)
        
        y1, y2 = ys.min(), ys.max()
        x1, x2 = xs.min(), xs.max()
        
        cropped = masked_region[y1:y2+1, x1:x2+1]
        
        return cropped
    
    def predict_finish(self, image_bgr: np.ndarray, mask: np.ndarray, region: str) -> Dict:
        masked_region = self._preprocess_masked_region(image_bgr, mask)
        
        if not self.use_cnn:
            finish, confidence = self._rule_based_fallback(masked_region, region)
            return {
                'finish': finish,
                'confidence': confidence,
                'method': 'rule_based'
            }
        
        try:
            rgb = cv2.cvtColor(masked_region, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)
            
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted_idx = torch.max(probabilities, 1)
            
            finish = IDX_TO_FINISH[predicted_idx.item()]
            confidence_score = confidence.item()
            
            if region == 'cheeks' and finish == 'glossy':
                finish = 'matte'
                confidence_score *= 0.8
            elif region == 'eyeshadow' and finish == 'glossy':
                finish = 'shimmer'
                confidence_score *= 0.8
            
            return {
                'finish': finish,
                'confidence': round(confidence_score, 3),
                'method': 'cnn',
                'all_probabilities': {
                    FINISH_CLASSES[i]: round(probabilities[0][i].item(), 3)
                    for i in range(len(FINISH_CLASSES))
                }
            }
        
        except Exception as e:
            print(f"⚠️  CNN 예측 실패, 규칙 기반 폴백: {e}")
            finish, confidence = self._rule_based_fallback(masked_region, region)
            return {
                'finish': finish,
                'confidence': confidence,
                'method': 'rule_based_fallback'
            }
    
    def predict_all_regions(self, image_bgr: np.ndarray, masks: Dict[str, np.ndarray]) -> Dict[str, Dict]:
        results = {}
        
        for region in ['lips', 'cheeks', 'eyeshadow']:
            if region in masks:
                results[region] = self.predict_finish(image_bgr, masks[region], region)
            else:
                results[region] = {
                    'finish': 'unknown',
                    'confidence': 0.0,
                    'method': 'no_mask'
                }
        
        return results


if __name__ == "__main__":
    print("=== Vision Encoder 테스트 ===\n")
    
    encoder = CNNVisionEncoder()
    
    print(f"사용 디바이스: {encoder.device}")
    print(f"CNN 사용 여부: {encoder.use_cnn}")
    print(f"분류 클래스: {FINISH_CLASSES}\n")
    
    dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    dummy_masks = {
        'lips': np.zeros((480, 640), dtype=np.uint8),
        'cheeks': np.zeros((480, 640), dtype=np.uint8),
        'eyeshadow': np.zeros((480, 640), dtype=np.uint8)
    }
    
    dummy_masks['lips'][200:280, 250:390] = 255
    dummy_masks['cheeks'][150:250, 100:200] = 255
    dummy_masks['cheeks'][150:250, 440:540] = 255
    dummy_masks['eyeshadow'][100:150, 230:280] = 255
    dummy_masks['eyeshadow'][100:150, 360:410] = 255
    
    print("더미 이미지 및 마스크로 테스트 실행...\n")
    
    results = encoder.predict_all_regions(dummy_image, dummy_masks)
    
    for region, result in results.items():
        print(f"[{region.upper()}]")
        print(f"  피니시: {result['finish']}")
        print(f"  신뢰도: {result['confidence']}")
        print(f"  방법: {result['method']}")
        if 'all_probabilities' in result:
            print(f"  전체 확률:")
            for finish, prob in result['all_probabilities'].items():
                print(f"    {finish}: {prob}")
        print()
    
    print("=== 테스트 완료 ===")