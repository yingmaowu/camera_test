import cv2
import numpy as np

color_map = {
    "黃色": {
        "comment": "火氣大，需調理肝膽系統",
        "advice": "飲食清淡，避免辛辣與油炸，檢查肝功能"
    },
    "白色厚重": {
        "comment": "濕氣重，可能為代謝循環不佳",
        "advice": "多運動、多喝水，保持口腔清潔"
    },
    "黑灰色": {
        "comment": "請留意嚴重疾病如腎病或癌症",
        "advice": "建議儘快就醫，進行專業診斷"
    },
    "正常舌色": {
        "comment": "正常紅舌或紅帶薄白，健康狀態",
        "advice": "保持良好作息與飲食，持續追蹤變化"
    }
}

def extract_tongue_mask(image_path):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    return img, mask

def detect_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return lap_var, lap_var < 80  # 門檻值可調整，越小越模糊

def analyze_image_color(image_path):
    img, mask = extract_tongue_mask(image_path)
    blur_score, is_blurred = detect_blur(img)
    if is_blurred:
        return "模糊", f"圖片模糊度過高（Laplacian={blur_score:.2f}）", "請重新拍照，保持穩定與對焦", (0, 0, 0)

    masked_pixels = img[mask > 0]
    if len(masked_pixels) < 100:
        return "非舌頭", "偵測到的舌頭面積過小", "請重新拍照，確保舌頭位於鏡頭中間並清晰", (0, 0, 0)

    # Lab 色彩分析
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    masked_lab_pixels = lab[mask > 0]
    avg_lab = np.mean(masked_lab_pixels, axis=0)
    L, A, B = map(int, avg_lab)

    # 分類判斷
    if A > 140 and L > 120:
        category = "正常舌色"
    elif B > 145 and L > 135:
        category = "黃色"
    elif L > 190 and A < 135:
        category = "白色厚重"
    elif L < 90 and A < 135 and B < 135:
        category = "黑灰色"
    else:
        return "未知", "無法判斷舌苔色彩", "請重新拍攝更清晰且光線正常的圖片", (L, A, B)

    info = color_map[category]
    return category, info["comment"], info["advice"], (L, A, B)
