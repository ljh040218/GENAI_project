# 📁 data_cosmetic 폴더 설명

이 폴더에는 화장품 제품별 데이터가 저장되어 있습니다.

## 구조
| 파일명 | 설명 |
|--------|------|
| `cheek.csv` | 블러셔 및 치크 제품 데이터 |
| `lip.csv` | 립 제품 데이터 |
| `eye.csv` | 아이섀도우 데이터 |

## 컬럼 정보 예시
- `brand`: 브랜드명 (예: 3CE, romand 등)
- `product_name`: 제품명
- `category`: 제품 카테고리 (cheek, lip 등)
- `shade_name`: 색상명
- `price`: 가격
- `finish`: 질감 정보 (매트, 글로시 등)
- `color_hex`: 색상 HEX 코드
- `lab_L`, `lab_a`, `lab_b`: CIELAB 색좌표

---

📌 **Note**
- 모든 CSV 파일은 UTF-8 인코딩으로 저장되어 있습니다.  
- `lab_*` 컬럼은 색상 분석 모델 입력용으로 사용됩니다.
