import cv2
import numpy as np

# 區域對應中文名稱
region_mapping = {
    "heart": "心",
    "liver": "肝",
    "spleen": "脾",
    "lung": "肺",
    "kidney": "腎"
}

# 五區中醫理論
theory_dict = {
    "heart": "心主血脈，舌尖對應心火",
    "liver": "肝藏血，舌邊對應肝膽",
    "spleen": "脾主運化，舌中對應脾胃",
    "lung": "肺朝百脈，舌尖側對應肺",
    "kidney": "腎藏精，舌根對應腎"
}

def apply_grayworld(image):
    b, g, r = cv2.split(image)
    avg_b, avg_g, avg_r = np.mean(b), np.mean(g), np.mean(r)
    avg_gray = (avg_b + avg_g + avg_r) / 3
    b = np.clip(b * (avg_gray / avg_b), 0, 255).astype(np.uint8)
    g = np.clip(g * (avg_gray / avg_g), 0, 255).astype(np.uint8)
    r = np.clip(r * (avg_gray / avg_r), 0, 255).astype(np.uint8)
    return cv2.merge([b, g, r])

def analyze_image_color(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img = apply_grayworld(img)
    avg_rgb = np.mean(img.reshape(-1, 3), axis=0).astype(int).tolist()
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

    h, w, _ = img.shape

    # 固定 overlay 座標切割 (依 overlay.png 設計)
    rois = {
        "heart": img[0:int(h*0.2), int(w*0.35):int(w*0.65)],
        "liver": img[int(h*0.2):int(h*0.5), 0:int(w*0.3)],
        "spleen": img[int(h*0.2):int(h*0.5), int(w*0.7):w],
        "lung": img[int(h*0.5):int(h*0.7), int(w*0.2):int(w*0.8)],
        "kidney": img[int(h*0.7):h, int(w*0.3):int(w*0.7)]
    }

    result = {}
    for region_id, roi in rois.items():
        roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
        avg_lab = np.mean(roi_lab.reshape(-1, 3), axis=0).tolist()

        result[region_id] = {
            "name": region_mapping[region_id],
            "avg_lab": [round(v) for v in avg_lab],
            "diagnosis": theory_dict[region_id]
        }

    return result
