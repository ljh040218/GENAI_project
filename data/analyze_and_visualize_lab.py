import csv
import cv2
import numpy as np
import os

LAB_DATA = """
1.jpg,lips,136.8,155.25,143.71
1.jpg,cheeks,171.88,143.01,143.36
1.jpg,eyeshadow,152.73,143.59,141.63
10.jpg,lips,149.63,159.77,147.29
10.jpg,cheeks,190.21,142.94,143.27
10.jpg,eyeshadow,147.02,143.63,142.16
11.jpg,lips,156.54,154.0,137.02
11.jpg,cheeks,203.37,139.1,133.55
11.jpg,eyeshadow,175.43,139.28,134.66
12.jpg,lips,150.39,161.55,151.35
12.jpg,cheeks,195.05,139.68,141.56
12.jpg,eyeshadow,171.03,142.69,144.94
13.jpg,lips,154.77,159.62,136.88
13.jpg,cheeks,207.61,137.38,134.56
13.jpg,eyeshadow,177.83,141.09,132.66
14.jpg,lips,162.86,157.54,138.82
14.jpg,cheeks,204.93,139.36,137.15
14.jpg,eyeshadow,191.03,139.43,137.29
15.jpg,lips,139.82,158.49,140.46
15.jpg,cheeks,197.29,137.53,140.44
15.jpg,eyeshadow,164.23,134.98,137.18
16.jpg,lips,115.87,158.68,151.91
16.jpg,cheeks,181.5,139.8,146.06
16.jpg,eyeshadow,148.25,142.4,145.64
17.jpg,lips,146.13,167.79,148.59
17.jpg,cheeks,185.21,141.16,139.23
17.jpg,eyeshadow,173.23,143.66,141.15
18.jpg,lips,133.09,156.1,145.38
18.jpg,cheeks,199.69,138.68,148.29
18.jpg,eyeshadow,158.1,139.1,145.85
19.jpg,lips,193.28,146.16,135.72
19.jpg,cheeks,214.91,134.6,135.37
19.jpg,eyeshadow,178.84,132.84,132.88
2.jpg,lips,114.7,154.58,149.1
2.jpg,cheeks,164.26,142.08,145.86
2.jpg,eyeshadow,147.8,141.81,146.19
20.jpg,lips,151.69,145.76,143.05
20.jpg,cheeks,187.18,134.86,140.32
20.jpg,eyeshadow,152.61,134.23,136.81
21.jpg,lips,117.58,152.97,143.8
21.jpg,cheeks,172.98,139.88,143.03
21.jpg,eyeshadow,148.04,139.45,139.19
22.jpg,lips,126.54,180.57,153.27
22.jpg,cheeks,187.78,145.35,144.46
22.jpg,eyeshadow,169.78,146.95,145.8
23.jpg,lips,140.67,165.91,148.36
23.jpg,cheeks,184.52,145.09,147.76
23.jpg,eyeshadow,144.86,147.04,148.68
24.jpg,lips,127.18,167.1,155.77
24.jpg,cheeks,176.06,142.62,143.35
24.jpg,eyeshadow,146.09,146.11,147.94
25.jpg,lips,116.72,155.34,146.9
25.jpg,cheeks,166.42,136.41,142.58
25.jpg,eyeshadow,148.98,136.06,143.35
26.jpg,lips,115.21,151.53,144.65
26.jpg,cheeks,158.02,141.91,145.79
26.jpg,eyeshadow,139.9,141.18,145.65
27.jpg,lips,134.12,149.37,140.55
27.jpg,cheeks,193.17,135.37,137.24
27.jpg,eyeshadow,156.41,137.83,136.77
28.jpg,lips,137.67,163.5,147.59
28.jpg,cheeks,199.89,139.1,139.84
28.jpg,eyeshadow,188.5,138.57,141.59
29.jpg,lips,123.21,160.06,148.52
29.jpg,cheeks,169.62,139.49,142.87
29.jpg,eyeshadow,153.18,140.45,144.8
3.jpg,lips,156.13,165.52,156.67
3.jpg,cheeks,195.5,140.68,144.46
3.jpg,eyeshadow,158.57,143.75,145.63
30.jpg,lips,140.09,158.29,146.47
30.jpg,cheeks,202.56,137.08,137.58
30.jpg,eyeshadow,159.62,141.35,138.51
31.jpg,lips,138.12,158.22,142.97
31.jpg,cheeks,159.48,145.28,147.48
31.jpg,eyeshadow,107.27,141.86,141.74
32.jpg,lips,100.55,172.19,153.24
32.jpg,cheeks,183.75,143.44,144.95
32.jpg,eyeshadow,170.59,144.13,145.03
33.jpg,lips,129.0,154.93,139.72
33.jpg,cheeks,188.6,140.72,138.65
33.jpg,eyeshadow,165.78,139.67,136.59
34.jpg,lips,174.4,154.81,147.12
34.jpg,cheeks,183.62,144.91,145.55
34.jpg,eyeshadow,174.42,142.94,146.27
35.jpg,lips,132.17,161.35,147.37
35.jpg,cheeks,185.13,140.73,143.32
35.jpg,eyeshadow,172.34,140.39,142.34
36.jpg,lips,113.01,160.27,150.91
36.jpg,cheeks,151.78,144.4,149.96
36.jpg,eyeshadow,142.32,142.77,148.8
37.jpg,lips,140.64,157.66,140.45
37.jpg,cheeks,183.76,141.03,136.96
37.jpg,eyeshadow,171.38,142.49,138.51
38.jpg,lips,126.29,163.13,143.5
38.jpg,cheeks,191.96,141.36,140.03
38.jpg,eyeshadow,154.25,143.81,141.72
39.jpg,lips,130.52,159.8,146.21
39.jpg,cheeks,192.99,143.06,144.36
39.jpg,eyeshadow,155.57,141.94,141.05
4.jpg,lips,125.71,171.78,152.04
4.jpg,cheeks,185.38,147.23,145.61
4.jpg,eyeshadow,155.51,147.42,145.85
40.jpg,lips,128.78,169.14,130.68
40.jpg,cheeks,193.58,139.39,139.41
40.jpg,eyeshadow,186.42,138.55,140.03
41.jpg,lips,125.34,167.23,147.26
41.jpg,cheeks,196.86,137.09,142.03
41.jpg,eyeshadow,174.96,137.19,141.63
42.jpg,lips,114.82,160.46,143.21
42.jpg,cheeks,172.37,144.21,140.96
42.jpg,eyeshadow,138.41,142.27,141.85
43.jpg,lips,114.2,154.75,146.55
43.jpg,cheeks,163.51,141.0,140.84
43.jpg,eyeshadow,125.76,143.58,142.09
44.png,lips,208.55,146.33,131.4
44.png,cheeks,225.69,132.81,133.16
44.png,eyeshadow,207.42,135.95,133.72
45.png,lips,139.21,160.63,123.66
45.png,cheeks,194.89,134.33,126.76
45.png,eyeshadow,143.4,136.89,125.58
46.png,lips,118.18,161.04,144.62
46.png,cheeks,159.94,145.09,145.56
46.png,eyeshadow,153.85,144.15,145.37
47.png,lips,105.03,164.71,143.85
47.png,cheeks,164.56,143.42,139.46
47.png,eyeshadow,140.44,142.13,140.52
48.png,lips,104.03,155.3,148.35
48.png,cheeks,177.27,141.68,143.54
48.png,eyeshadow,151.77,143.09,144.88
49.png,lips,119.47,161.42,140.3
49.png,cheeks,174.63,141.2,137.72
49.png,eyeshadow,158.78,142.88,139.4
5.jpg,lips,103.35,153.11,143.12
5.jpg,cheeks,158.02,138.12,137.05
5.jpg,eyeshadow,141.36,138.74,137.83
50.png,lips,145.79,156.39,148.49
50.png,cheeks,186.05,141.57,145.41
50.png,eyeshadow,150.63,145.08,146.87
51.png,lips,118.32,151.18,142.77
51.png,cheeks,191.78,135.97,144.2
51.png,eyeshadow,155.8,135.95,144.07
52.png,lips,99.5,154.57,140.81
52.png,cheeks,154.57,139.81,139.69
52.png,eyeshadow,134.77,140.15,139.8
53.jpg,lips,142.25,162.02,143.32
53.jpg,cheeks,172.63,139.06,140.39
53.jpg,eyeshadow,178.8,139.92,141.28
54.png,lips,121.45,149.0,127.98
54.png,cheeks,163.08,134.26,129.0
54.png,eyeshadow,136.74,132.16,129.99
6.jpg,lips,131.25,156.9,142.77
6.jpg,cheeks,168.16,141.06,141.96
6.jpg,eyeshadow,130.55,137.07,145.52
7.jpg,lips,168.06,155.95,151.35
7.jpg,cheeks,182.36,138.59,149.2
7.jpg,eyeshadow,151.83,136.7,145.13
8.jpg,lips,107.69,154.28,136.06
8.jpg,cheeks,183.67,138.73,133.79
8.jpg,eyeshadow,143.54,139.99,134.43
9.jpg,lips,117.52,163.35,145.45
9.jpg,cheeks,192.99,141.92,142.1
9.jpg,eyeshadow,186.37,142.92,143.53
"""

def check_lab_values():
    lines = LAB_DATA.strip().split('\n')
    
    print("="*70)
    print("LAB 값 유효성 검사")
    print("="*70)
    
    errors = []
    warnings = []
    
    for line in lines:
        if not line.strip():
            continue
        parts = line.strip().split(',')
        if len(parts) != 5:
            continue
        
        filename, region, L, a, b = parts[0], parts[1], float(parts[2]), float(parts[3]), float(parts[4])
        
        if L < 0 or L > 255:
            errors.append(f"{filename} {region}: L 값 범위 오류 ({L})")
        elif L > 100:
            warnings.append(f"{filename} {region}: L 값이 100 초과 ({L:.2f}) - LAB 공간에서는 0-100이 정상")
        
        if a < 0 or a > 255:
            errors.append(f"{filename} {region}: a 값 범위 오류 ({a})")
        
        if b < 0 or b > 255:
            errors.append(f"{filename} {region}: b 값 범위 오류 ({b})")
    
    if errors:
        print("\n심각한 오류:")
        for error in errors:
            print(f"  {error}")
    else:
        print("\n심각한 오류: 없음")
    
    if warnings:
        print("\n경고:")
        for warning in warnings:
            print(f"  {warning}")
        print("\n분석: LAB 값이 OpenCV의 0-255 스케일로 저장되어 있습니다.")
        print("       L: 0-100 범위를 0-255로 스케일링")
        print("       a, b: -128~127 범위를 0-255로 스케일링 (128이 중심)")
    else:
        print("\n경고: 없음")
    
    print("\n" + "="*70)
    return len(errors) == 0

def lab_to_rgb(L, a, b):
    lab_pixel = np.uint8([[[L, a, b]]])
    bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)[0][0]
    rgb = (int(bgr_pixel[2]), int(bgr_pixel[1]), int(bgr_pixel[0]))
    return rgb

def lab_to_hex(L, a, b):
    r, g, b_val = lab_to_rgb(L, a, b)
    return f"#{r:02x}{g:02x}{b_val:02x}"

def get_color_description(L, a, b):
    if L < 70:
        brightness = "어두운"
    elif L < 120:
        brightness = "중간"
    elif L < 180:
        brightness = "밝은"
    else:
        brightness = "매우 밝은"
    
    if abs(a - 128) < 15 and abs(b - 128) < 15:
        return f"{brightness} 무채색"
    
    hue_desc = []
    if a > 155:
        hue_desc.append("빨강")
    elif a < 100:
        hue_desc.append("초록")
    
    if b > 155:
        hue_desc.append("노랑")
    elif b < 100:
        hue_desc.append("파랑")
    
    if len(hue_desc) == 0:
        return f"{brightness} 중성"
    
    return f"{brightness} {'+'.join(hue_desc)}"

def save_to_csv(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Image', 'Region', 'L', 'a', 'b', 'RGB_R', 'RGB_G', 'RGB_B', 'HEX', 'Description'])
        
        lines = LAB_DATA.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
            parts = line.strip().split(',')
            if len(parts) != 5:
                print(f"Warning: Skipping invalid line (expected 5 parts, got {len(parts)}): {line}")
                continue
            
            filename = parts[0]
            region = parts[1]
            L = float(parts[2])
            a = float(parts[3])
            b = float(parts[4])
            
            rgb = lab_to_rgb(L, a, b)
            hex_code = lab_to_hex(L, a, b)
            desc = get_color_description(L, a, b)
            
            writer.writerow([
                filename, region, 
                f"{L:.2f}", f"{a:.2f}", f"{b:.2f}",
                rgb[0], rgb[1], rgb[2],
                hex_code, desc
            ])
    
    print(f"\nCSV 저장 완료: {output_path}")

def generate_html(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>얼굴 메이크업 ROI 색상 분석</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            padding: 20px; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            margin: 0;
        }
        h1 { 
            text-align: center; 
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stats h2 {
            margin-top: 0;
            color: #34495e;
        }
        .image-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .image-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .regions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .region-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        .region-card.lips { border-left-color: #e74c3c; }
        .region-card.cheeks { border-left-color: #f39c12; }
        .region-card.eyeshadow { border-left-color: #9b59b6; }
        .region-name {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
            text-transform: uppercase;
        }
        .color-swatch {
            width: 100%;
            height: 80px;
            border-radius: 6px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            border: 1px solid #ddd;
        }
        .color-info {
            font-size: 0.85em;
            color: #555;
            margin: 5px 0;
            font-family: 'Courier New', monospace;
        }
        .color-desc {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 8px;
            font-style: italic;
        }
        .legend {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>얼굴 메이크업 ROI 색상 분석</h1>
    <div class="subtitle">MediaPipe 얼굴 파싱을 통한 립, 치크, 아이섀도우 영역 LAB 색상 추출</div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background-color: #e74c3c;"></div>
            <span>립 (Lips)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #f39c12;"></div>
            <span>치크 (Cheeks)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #9b59b6;"></div>
            <span>아이섀도우 (Eyeshadow)</span>
        </div>
    </div>
"""
    
    lines = LAB_DATA.strip().split('\n')
    current_image = None
    image_data = {}
    
    for line in lines:
        if not line.strip():
            continue
        parts = line.strip().split(',')
        if len(parts) != 5:
            continue
        
        filename, region, L, a, b = parts[0], parts[1], float(parts[2]), float(parts[3]), float(parts[4])
        
        if filename not in image_data:
            image_data[filename] = {}
        
        image_data[filename][region] = {
            'L': L, 'a': a, 'b': b,
            'rgb': lab_to_rgb(L, a, b),
            'hex': lab_to_hex(L, a, b),
            'desc': get_color_description(L, a, b)
        }
    
    for idx, (filename, regions) in enumerate(sorted(image_data.items()), 1):
        html += f"""
    <div class="image-section">
        <div class="image-title">{idx}. {filename}</div>
        <div class="regions">
"""
        
        region_order = ['lips', 'cheeks', 'eyeshadow']
        region_names = {
            'lips': '립 (Lips)',
            'cheeks': '치크 (Cheeks)',
            'eyeshadow': '아이섀도우 (Eyeshadow)'
        }
        
        for region in region_order:
            if region in regions:
                data = regions[region]
                html += f"""
            <div class="region-card {region}">
                <div class="region-name">{region_names[region]}</div>
                <div class="color-swatch" style="background-color: {data['hex']};"></div>
                <div class="color-info">LAB: L={data['L']:.1f}, a={data['a']:.1f}, b={data['b']:.1f}</div>
                <div class="color-info">RGB: ({data['rgb'][0]}, {data['rgb'][1]}, {data['rgb'][2]})</div>
                <div class="color-info">HEX: {data['hex']}</div>
                <div class="color-desc">{data['desc']}</div>
            </div>
"""
        
        html += """
        </div>
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML 저장 완료: {output_path}")

if __name__ == "__main__":
    print("얼굴 메이크업 ROI LAB 색상 분석\n")
    
    is_valid = check_lab_values()
    
    if is_valid:
        print("\n처리를 계속합니다...\n")
    else:
        print("\n경고: 오류가 있지만 계속 진행합니다.\n")
    
    csv_path = "/home/jeongmin/genai/debug_out/lab_colors.csv"
    html_path = "/home/jeongmin/genai/debug_out/lab_colors.html"
    
    save_to_csv(csv_path)
    generate_html(html_path)
    
    print("\n완료!")
    print(f"CSV: {csv_path}")
    print(f"HTML: {html_path}")
