import cv2
import numpy as np

# 舌苔五區對應中醫理論與建議
REGION_THEORY = {
    "心肺": "舌尖代表心肺功能，紅潤正常，偏紅可能火氣旺。",
    "肝膽": "舌邊屬肝膽，紅紫為肝火，齒痕為脾虛。",
    "脾胃": "舌中對應脾胃，苔厚黃表示濕熱。",
    "腎": "舌根代表腎，黑苔灰苔顯示腎氣不足。"
}

REGION_ADVICE_RULE = {
    "心肺": {"偏紅": "避免熬夜與過度壓力，多喝溫水。", "其他": "維持規律作息與心情平穩。"},
    "肝膽": {"偏紫": "注意疏肝解鬱，避免暴怒與壓力。", "其他": "保持情緒舒暢，避免油炸物。"},
    "脾胃": {"偏黃": "脾胃濕熱，少吃油膩甜食，多運動。", "其他": "飲食均衡，避免暴飲暴食。"},
    "腎": {"偏黑灰": "腎氣不足，注意保暖，早睡避免疲勞。", "其他": "作息規律，避免久坐。"}
}

# 定義 overlay.png 中的五區顏色對應（BGR）
COLOR_TO_REGION = {
    (255, 0, 0): "腎",         # 藍色區塊
    (0, 255, 0): "脾胃",       # 綠色區塊
    (0, 255, 255): "心肺",     # 亮綠色（黃色）
    (128, 128, 128): "肝膽"    # 灰色區塊（左右皆視為肝膽）
}

# LAB 判斷規則
def diagnose_region(L, A, B):
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

def analyze_tongue_regions_with_overlay(photo_path, overlay_path="static/TongueOverlay.png"):
    tongue_img = cv2.imread(photo_path)
    overlay_img = cv2.imread(overlay_path)

    if tongue_img is None or overlay_img is None:
        raise FileNotFoundError("❌ 無法讀取圖像或 overlay.png")

    if tongue_img.shape != overlay_img.shape:
        overlay_img = cv2.resize(overlay_img, (tongue_img.shape[1], tongue_img.shape[0]))

    region_dict = {}

    for color_bgr, region_name in COLOR_TO_REGION.items():
        mask = cv2.inRange(overlay_img, np.array(color_bgr), np.array(color_bgr))
        mask_indices = np.where(mask == 255)

        if len(mask_indices[0]) == 0:
            continue

        tongue_lab = cv2.cvtColor(tongue_img, cv2.COLOR_BGR2LAB)
        selected_pixels = tongue_lab[mask_indices]
        avg_lab = np.mean(selected_pixels, axis=0)
        L, A, B = avg_lab

        diagnosis = diagnose_region(L, A, B)
        theory = REGION_THEORY.get(region_name, "無理論")
        advice = REGION_ADVICE_RULE.get(region_name, {}).get(diagnosis, REGION_ADVICE_RULE.get(region_name, {}).get("其他", "保持良好作息"))

        region_dict[region_name] = {
            "區域": region_name,
            "診斷": diagnosis,
            "理論": theory,
            "建議": advice
        }

    return region_dict
