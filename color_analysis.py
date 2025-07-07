import cv2
import numpy as np
import os

def analyze_image_color(image_path):
    img = cv2.imread(image_path)
    avg_rgb = np.mean(img.reshape(-1,3), axis=0).astype(int).tolist()
    r, g, b = avg_rgb

    if r > 150 and g < 100:
        main_color = "偏紅"
        comment = "舌質偏紅，可能有火氣"
        advice = "多喝水，避免辛辣"
    elif r > 200 and g > 150:
        main_color = "淡紅"
        comment = "正常舌色"
        advice = "維持現有作息"
    else:
        main_color = "其他"
        comment = "無法明確判斷"
        advice = "建議諮詢專業醫師"

    return main_color, comment, advice, avg_rgb

def analyze_tongue_regions(image_path):
    img = cv2.imread(image_path)
    h, w, _ = img.shape

    # 固定 overlay 座標切割 (五區)
    regions = {
        "heart": img[h//5:2*h//5, w//3:2*w//3],
        "lung": img[:h//5, w//3:2*w//3],
        "liver": img[2*h//5:3*h//5, :w//3],
        "spleen": img[2*h//5:3*h//5, 2*w//3:],
        "kidney": img[4*h//5:, w//3:2*w//3]
    }

    results = {}
    for name, roi in regions.items():
        avg_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).reshape(-1,3).mean(axis=0).tolist()
        diagnosis = "正常"
        results[name] = {"name": name, "avg_lab": avg_lab, "diagnosis": diagnosis}

    # 產生 processed 標記圖
    overlay = img.copy()
    for name, roi in regions.items():
        x1, y1 = w//3, h//5
        x2, y2 = 2*w//3, 2*h//5
        cv2.rectangle(overlay, (x1,y1), (x2,y2), (0,0,255), 2)

    processed_path = f"static/processed/{os.path.basename(image_path)}"
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    cv2.imwrite(processed_path, overlay)

    return results, processed_path
