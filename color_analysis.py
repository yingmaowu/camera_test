import cv2
import numpy as np

REGION_THEORY = {
    "心": "舌尖代表心肺功能，紅潤正常，偏紅可能火氣旺。",
    "肝": "舌邊屬肝膽，紅紫為肝火，齒痕為脾虛。",
    "脾": "舌中對應脾胃，苔厚黃表示濕熱。",
    "肺": "舌前屬肺，白苔為正常，黃苔為肺熱。",
    "腎": "舌根代表腎，黑苔灰苔顯示腎氣不足。"
}

REGION_ADVICE_RULE = {
    "心": {
        "偏紅": "避免熬夜與過度壓力，多喝溫水。",
        "其他": "維持規律作息與心情平穩。"
    },
    "肝": {
        "偏紫": "注意疏肝解鬱，避免暴怒與壓力。",
        "其他": "保持情緒舒暢，避免油炸物。"
    },
    "脾": {
        "偏黃": "脾胃濕熱，少吃油膩甜食，多運動。",
        "其他": "飲食均衡，避免暴飲暴食。"
    },
    "肺": {
        "偏黃": "肺熱，避免辛辣煎炸，多喝水。",
        "其他": "保持空氣流通，避免吸菸。"
    },
    "腎": {
        "偏黑灰": "腎氣不足，注意保暖，早睡避免疲勞。",
        "其他": "作息規律，避免久坐。"
    }
}

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

def diagnose_region(L, A, B):
    if A > 145 and B < 150 and L > 120:
        return "正常"
    elif B > 150 and A > 140 and L > 130:
        return "偏黃"
    elif L > 190 and A < 135:
        return "白苔"
    elif L < 90 and A < 130 and B < 130:
        return "偏黑灰"
    elif A > 160:
        return "偏紅"
    elif A > 150:
        return "偏紫"
    else:
        return "其他"

def analyze_tongue_regions(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img = apply_grayworld(img)
    img = apply_CLAHE(img)

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    h, w, _ = img.shape

    # ➡️ 讀取 overlay mask
    overlay = cv2.imread("static/overlay.png", cv2.IMREAD_UNCHANGED)
    overlay = cv2.resize(overlay, (w, h), interpolation=cv2.INTER_NEAREST)
    mask = overlay[:, :, 3]  # alpha channel

    # ➡️ 定義中文區域 mapping 與 ROI 區塊
    region_rois = {
        "心": (slice(0, h//3), slice(w//3, 2*w//3)),
        "肝": (slice(h//3, 2*h//3), slice(0, w//3)),
        "脾": (slice(h//3, 2*h//3), slice(2*w//3, w)),
        "肺": (slice(0, h//3), slice(0, w//3)),
        "腎": (slice(2*h//3, h), slice(w//3, 2*w//3)),
    }

    results = {}
    for region, (ys, xs) in region_rois.items():
        roi_lab = img_lab[ys, xs]
        roi_mask = mask[ys, xs]
        valid_pixels = roi_lab[roi_mask > 0]

        if len(valid_pixels) == 0:
            avg_lab = [0,0,0]
            diagnosis = "無法判斷"
            advice = "建議重新拍攝"
        else:
            avg_lab = np.mean(valid_pixels, axis=0)
            L, A, B = avg_lab
            diagnosis = diagnose_region(L, A, B)
            advice = REGION_ADVICE_RULE.get(region, {}).get(diagnosis, "維持良好作息")

        results[region] = {
            "區域": region,
            "avg_lab": [int(avg_lab[0]), int(avg_lab[1]), int(avg_lab[2])],
            "診斷": diagnosis,
            "理論": REGION_THEORY.get(region, "無理論"),
            "建議": advice
        }

    return results
