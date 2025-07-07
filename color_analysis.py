import cv2
import numpy as np

def apply_grayworld(image):
    b, g, r = cv2.split(image)
    avg_b, avg_g, avg_r = np.mean(b), np.mean(g), np.mean(r)
    avg_gray = (avg_b + avg_g + avg_r) / 3
    b = np.clip(b * (avg_gray / avg_b), 0, 255).astype(np.uint8)
    g = np.clip(g * (avg_gray / avg_g), 0, 255).astype(np.uint8)
    r = np.clip(r * (avg_gray / avg_r), 0, 255).astype(np.uint8)
    return cv2.merge([b, g, r])

def apply_CLAHE(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l,a,b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def analyze_image_color(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img = apply_grayworld(img)
    img = apply_CLAHE(img)

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
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    h, w, _ = img.shape

    # 固定五區 ROI 定義 (以你舌頭 overlay 對應)
    rois = {
        "heart": img_lab[int(h*0.15):int(h*0.30), int(w*0.40):int(w*0.60)],
        "lung": img_lab[int(h*0.05):int(h*0.20), int(w*0.30):int(w*0.70)],
        "liver": img_lab[int(h*0.30):int(h*0.50), int(w*0.00):int(w*0.30)],
        "spleen": img_lab[int(h*0.30):int(h*0.50), int(w*0.70):int(w*1.00)],
        "kidney": img_lab[int(h*0.50):int(h*0.80), int(w*0.30):int(w*0.70)]
    }

    result = {}
    for region_name, roi_lab in rois.items():
        avg_lab = np.mean(roi_lab.reshape(-1, 3), axis=0).tolist()
        L, A, B = map(int, avg_lab)

        # 簡單診斷判斷
        if A > 145 and B < 150 and L > 120:
            diagnosis = "正常"
        elif B > 150 and A > 140 and L > 130:
            diagnosis = "偏黃，火氣旺"
        elif L > 190 and A < 135:
            diagnosis = "白苔，脾胃虛寒"
        elif L < 90 and A < 130 and B < 130:
            diagnosis = "偏黑灰，腎氣不足"
        else:
            diagnosis = "未知"

        result[region_name] = {
            "name": region_name,
            "avg_lab": avg_lab,
            "diagnosis": diagnosis
        }

    return result
