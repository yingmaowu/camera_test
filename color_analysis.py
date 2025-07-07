import cv2
import numpy as np

# 直接定義五區中文 mapping 與五區中醫理論判斷函式
REGION_MAPPING = {
    "heart": "心",
    "lung": "肺",
    "liver": "肝",
    "spleen": "脾",
    "kidney": "腎"
}

def diagnose_lab(l, a, b, region_name):
    """
    根據 L, A, B 值給出每區的中醫推論與建議。
    實際邏輯可依臨床經驗修改，以下為範例邏輯：
    """
    if l > 190 and a < 135:
        diagnosis = f"{region_name}區偏白，脾胃虛寒"
        advice = "可多吃溫補食物，如薑茶"
    elif a > 145 and b < 150 and l > 120:
        diagnosis = f"{region_name}區偏紅，火氣偏旺"
        advice = "多喝水，避免辛辣刺激"
    elif b > 150 and a > 140 and l > 130:
        diagnosis = f"{region_name}區偏黃，體內濕熱"
        advice = "可飲菊花茶或綠茶清熱"
    elif l < 90 and a < 130 and b < 130:
        diagnosis = f"{region_name}區偏黑灰，腎氣不足"
        advice = "建議充足睡眠與補腎飲食"
    else:
        diagnosis = f"{region_name}區正常或無特殊異常"
        advice = "維持現有作息與飲食"

    return diagnosis, advice

def analyze_tongue_regions(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    h, w, _ = img.shape

    # 固定 overlay 五區切割（示例比例，可依 overlay 設計微調）
    rois = {
        "heart": img_lab[h//4:h//2, w//3:2*w//3],  # 中間偏上
        "lung": img_lab[h//8:h//4, w//4:3*w//4],   # 最上方
        "liver": img_lab[h//2:5*h//8, w//4:w//2],  # 左下
        "spleen": img_lab[h//2:5*h//8, w//2:3*w//4],  # 右下
        "kidney": img_lab[5*h//8:3*h//4, w//3:2*w//3]  # 最下方
    }

    result = {}
    for region_id, roi_lab in rois.items():
        avg_lab = np.mean(roi_lab.reshape(-1, 3), axis=0).tolist()
        l, a, b = map(int, avg_lab)

        diagnosis, advice = diagnose_lab(l, a, b, REGION_MAPPING[region_id])

        result[region_id] = {
            "name": REGION_MAPPING[region_id],
            "avg_lab": [l, a, b],
            "diagnosis": diagnosis,
            "advice": advice
        }

    return result

def analyze_image_color(image_path):
    """
    提供整體舌苔主色推論，可搭配五區推論同時顯示於 index Swal
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_lab = np.mean(img_lab.reshape(-1,3), axis=0)
    l, a, b = map(int, avg_lab)

    if l > 190 and a < 135:
        main_color = "白苔"
        comment = "舌質偏白，脾胃虛寒"
        advice = "可多吃溫補食物，如薑茶"
    elif a > 145 and b < 150 and l > 120:
        main_color = "紅苔"
        comment = "舌質偏紅，火氣較旺"
        advice = "多喝水，避免辛辣刺激"
    elif b > 150 and a > 140 and l > 130:
        main_color = "黃苔"
        comment = "舌苔偏黃，體內濕熱"
        advice = "可飲菊花茶或綠茶清熱"
    elif l < 90 and a < 130 and b < 130:
        main_color = "黑苔"
        comment = "舌苔偏黑灰，腎氣不足"
        advice = "建議充足睡眠與補腎飲食"
    else:
        main_color = "其他"
        comment = "無法明確判斷"
        advice = "建議諮詢中醫師進一步診斷"

    return main_color, comment, advice, [l, a, b]
