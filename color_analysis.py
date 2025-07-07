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
        "無明顯症狀": "維持規律作息與心情平穩。"
    },
    "肝": {
        "偏紫": "注意疏肝解鬱，避免暴怒與壓力。",
        "無明顯症狀": "保持情緒舒暢，避免油炸物。"
    },
    "脾": {
        "偏黃": "脾胃濕熱，少吃油膩甜食，多運動。",
        "無明顯症狀": "飲食均衡，避免暴飲暴食。"
    },
    "肺": {
        "偏黃": "肺熱，避免辛辣煎炸，多喝水。",
        "無明顯症狀": "保持空氣流通，避免吸菸。"
    },
    "腎": {
        "偏黑灰": "腎氣不足，注意保暖，早睡避免疲勞。",
        "無明顯症狀": "作息規律，避免久坐。"
    }
}

def diagnose_region(L, A, B, region):
    # 更新診斷條件以提升精準度
    if A > 145 and B < 150 and L > 120:
        return "健康"
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
        return "無明顯症狀"

def analyze_image_color(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_lab = np.mean(img_lab.reshape(-1,3), axis=0)
    L, A, B = avg_lab

    if A > 145 and B < 150 and L > 120:
        return "偏紅", "舌質偏紅，可能有火氣", "多喝水，避免辛辣", [int(L),int(A),int(B)]
    elif B > 150 and A > 140 and L > 130:
        return "偏黃", "舌苔偏黃，可能脾胃濕熱", "少吃油膩甜食", [int(L),int(A),int(B)]
    elif L > 190 and A < 135:
        return "白苔", "舌苔偏白，可能虛寒", "注意保暖", [int(L),int(A),int(B)]
    elif L < 90 and A < 130 and B < 130:
        return "偏黑灰", "舌苔偏黑灰，腎氣不足", "早睡避免疲勞", [int(L),int(A),int(B)]
    else:
        return "無明顯異常", "無明顯異常", "維持現有作息", [int(L),int(A),int(B)]

def analyze_tongue_regions(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    h, w, _ = img.shape

    rois = {
        "心": img_lab[0:h//3, w//3:2*w//3],
        "肝": img_lab[h//3:2*h//3, 0:w//3],
        "脾": img_lab[h//3:2*h//3, 2*w//3:w],
        "肺": img_lab[0:h//3, 0:w//3],
        "腎": img_lab[2*h//3:h, w//3:2*w//3],
    }

    results = {}
    for region_name, roi_lab in rois.items():
        avg_lab = np.mean(roi_lab.reshape(-1,3), axis=0)
        L, A, B = avg_lab
        diagnosis = diagnose_region(L, A, B, region_name)

        # 若診斷為其他，統一顯示「無明顯症狀」
        display_diagnosis = "無明顯症狀" if diagnosis == "其他" else diagnosis

        advice = REGION_ADVICE_RULE.get(region_name, {}).get(display_diagnosis, "保持良好作息")

        results[region_name] = {
            "區域": region_name,
            "診斷": display_diagnosis,
            "理論": REGION_THEORY.get(region_name, "無理論"),
            "建議": advice
        }

    return results
