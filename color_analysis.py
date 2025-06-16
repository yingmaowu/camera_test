import cv2
import numpy as np
from PIL import Image

# 舌苔色彩對應中醫建議
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

def analyze_image_color(image_path):
    img, mask = extract_tongue_mask(image_path)
    masked_pixels = img[mask > 0]

    if len(masked_pixels) < 100:
        return "非舌頭", "偵測到的舌頭面積過小", "請重新拍照，確保舌頭位於鏡頭中間並清晰", (0, 0, 0)

    avg_color = np.mean(masked_pixels, axis=0)
    r, g, b = map(int, avg_color[::-1])  # BGR to RGB

    brightness = (r + g + b) / 3
    if r > 130 and g < 140 and b < 140 and brightness < 190:
        category = "正常舌色"
    elif r > 140 and g > 110 and b < 100 and brightness > 150:
        category = "黃色"
    elif brightness > 180 and min(r, g, b) > 160:
        category = "白色厚重"
    elif brightness < 100 and max(abs(r - g), abs(g - b), abs(r - b)) < 60:
        category = "黑灰色"
    else:
        return "未知", "無法判斷", "請重新拍攝更清晰的圖片", (r, g, b)

    info = color_map[category]
    return category, info["comment"], info["advice"], (r, g, b)
