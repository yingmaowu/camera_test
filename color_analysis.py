from PIL import Image
import numpy as np

# 顏色對應的中醫解釋
color_map = {
    "黃色": "火氣大，需調理肝膽系統",
    "白色厚重": "濕氣重，可能為代謝循環不佳",
    "黑灰色": "請留意嚴重疾病如腎病或癌症",
    "正常舌色": "正常紅舌或紅帶薄白，健康狀態"
}

# 分類條件（用平均 RGB 決定主色）
def determine_category_from_rgb(r, g, b):
    brightness = (r + g + b) / 3

    # 正常舌色：偏紅但不太亮、藍值不高（微粉紅）
    if r > 130 and g < 140 and b < 140 and brightness < 190:
        return "正常舌色"

    # 黃色：紅綠高但藍明顯低（橘黃）、整體亮一點
    elif r > 140 and g > 110 and b < 100 and brightness > 150:
        return "黃色"

    # 白色厚重：整體亮、RGB 相對接近且偏白
    elif brightness > 180 and min(r, g, b) > 160:
        return "白色厚重"

    # 黑灰色：偏暗、RGB 接近（灰、黑、深紅）
    elif brightness < 100 and max(abs(r - g), abs(g - b), abs(r - b)) < 60:
        return "黑灰色"

    else:
        return "未知"


# 主函式：回傳分類、推論與主色 RGB
def analyze_image_color(image_path):
    image = Image.open(image_path).convert("RGB")
    resized = image.resize((50, 50))
    npimg = np.array(resized)

    # 只取中間 1/3 區域
    h, w, _ = npimg.shape
    crop = npimg[h//3:h*2//3, w//3:w*2//3]

    avg = np.mean(crop.reshape(-1, 3), axis=0)
    r, g, b = map(int, avg)

    category = determine_category_from_rgb(r, g, b)
    meaning = color_map.get(category, "無法判斷")

    print(f"🎯 RGB({r}, {g}, {b}) → 主色分類：{category}")
    return category, meaning, (r, g, b)
