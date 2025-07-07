# color_analysis.py

import cv2
import numpy as np
import sys

# 🗂️ 五區 ID 與中文名稱對應 table
region_mapping = {
    "liver": "肝",
    "kidney": "腎",
    "heart": "心",
    "spleen": "脾胃",
    "lung": "肺"
}

def analyze_tongue_regions(image_path):
    """
    分析舌頭五區 LAB 與 HSV 平均，回傳診斷結果 dict
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # 🔖 以圖像高寬切分 ROI (後續可改用 mask)
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
        # LAB 轉 BGR 再轉 HSV
        roi_bgr = cv2.cvtColor(roi_lab, cv2.COLOR_LAB2BGR)
        roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

        avg_lab = np.mean(roi_lab.reshape(-1, 3), axis=0).tolist()
        avg_hsv = np.mean(roi_hsv.reshape(-1, 3), axis=0).tolist()

        diagnosis = diagnose_region(avg_lab, avg_hsv)

        result[region_id] = {
            "name": region_mapping[region_id],
            "avg_lab": avg_lab,
            "avg_hsv": avg_hsv,
            "diagnosis": diagnosis
        }

    return result

def diagnose_region(avg_lab, avg_hsv):
    """
    根據 LAB / HSV 平均值，簡易判斷五區狀況
    """
    L, A, B = avg_lab
    if B > 150:
        return "濕熱"
    elif L < 50:
        return "陰虛"
    else:
        return "正常"

if __name__ == "__main__":
    """
    🧪 範例執行：
    python color_analysis.py test.jpg
    """
    if len(sys.argv) < 2:
        print("⚠️ 請輸入圖片路徑，例如: python color_analysis.py test.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    try:
        analysis = analyze_tongue_regions(image_path)
        for region, info in analysis.items():
            print(f"{info['name']} ({region}): {info['diagnosis']}")
            print(f"  平均 LAB: {info['avg_lab']}")
            print(f"  平均 HSV: {info['avg_hsv']}")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
