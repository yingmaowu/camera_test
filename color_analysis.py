import cv2
import numpy as np
import sys
from tongue_regions import REGION_MAP as region_mapping

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

def extract_tongue_mask(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    return cv2.bitwise_or(mask1, mask2)

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

def analyze_five_regions(image_path):
    img = cv2.imread(image_path)
    img = apply_grayworld(img)
    img = apply_CLAHE(img)

    mask = extract_tongue_mask(img)
    if np.sum(mask > 0) < 100:
        print("⚠️ 舌頭有效面積過小")
        return {"error": "舌頭面積過小"}

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    tongue_lab = lab[mask > 0]

    pixel_count = len(tongue_lab)
    print(f"舌頭整體有效像素數 = {pixel_count}")

    if pixel_count == 0:
        return {"error": "無有效舌頭像素"}

    avg_lab = np.mean(tongue_lab, axis=0)
    L, A, B = map(int, avg_lab)

    print(f"舌頭整體 L={L}, A={A}, B={B}")

    if A > 145 and B < 150 and L > 120:
        comment = "正常舌色"
    elif B > 150 and A > 140 and L > 130:
        comment = "偏黃，火氣較旺"
    elif L > 190 and A < 135:
        comment = "白苔，脾胃虛寒"
    elif L < 90 and A < 130 and B < 130:
        comment = "偏黑灰，腎氣不足"
    else:
        comment = "未知"

    results = {
        "整體分析": {
            "L": L,
            "A": A,
            "B": B,
            "推論": comment
        }
    }

    return results

def analyze_tongue_regions(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    h, w, _ = img.shape

    rois = {
        "liver": img_lab[0:h//3, 0:w//2],
        "kidney": img_lab[2*h//3:h, 0:w//2],
        "heart": img_lab[h//3:2*h//3, w//3:2*w//3],
        "spleen": img_lab[2*h//3:h, w//2:w],
        "lung": img_lab[0:h//3, w//2:w]
    }

    result = {}
    for region_id, roi_lab in rois.items():
        roi_bgr = cv2.cvtColor(roi_lab, cv2.COLOR_LAB2BGR)
        roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

        avg_lab = np.mean(roi_lab.reshape(-1, 3), axis=0).tolist()
        avg_hsv = np.mean(roi_hsv.reshape(-1, 3), axis=0).tol
