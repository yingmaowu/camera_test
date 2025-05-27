from PIL import Image
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

def determine_category_from_rgb(r, g, b):
    brightness = (r + g + b) / 3
    if r > 130 and g < 140 and b < 140 and brightness < 190:
        return "正常舌色"
    elif r > 140 and g > 110 and b < 100 and brightness > 150:
        return "黃色"
    elif brightness > 180 and min(r, g, b) > 160:
        return "白色厚重"
    elif brightness < 100 and max(abs(r - g), abs(g - b), abs(r - b)) < 60:
        return "黑灰色"
    else:
        return "未知"

def is_majority_tongue_like(crop, threshold=0.2):
    reshaped = crop.reshape(-1, 3)
    count = 0
    for pixel in reshaped:
        r, g, b = pixel
        brightness = (r + g + b) / 3
        if (
            r > 120 and
            60 < g < 140 and
            60 < b < 140 and
            100 < brightness < 220
        ):
            count += 1
    ratio = count / len(reshaped)
    return ratio >= threshold, ratio

def analyze_image_color(image_path):
    image = Image.open(image_path).convert("RGB")
    resized = image.resize((50, 50))
    npimg = np.array(resized)

    h, w, _ = npimg.shape
    crop = npimg[h//3:h*2//3, w//3:w*2//3]

    avg = np.mean(crop.reshape(-1, 3), axis=0)
    r, g, b = map(int, avg)

    sufficient, ratio = is_majority_tongue_like(crop, threshold=0.45)
    if not sufficient:
        return "非舌頭", f"舌頭比例過低（{round(ratio*100, 2)}%）", "請重新拍照，確保舌頭完整位於九宮格內", (r, g, b)

    category = determine_category_from_rgb(r, g, b)
    info = color_map.get(category, {"comment": "無法判斷", "advice": "請重新拍照"})

    return category, info["comment"], info["advice"], (r, g, b)
