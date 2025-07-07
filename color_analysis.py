import cv2
import numpy as np

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

def analyze_image_color(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片: {image_path}")

    img = apply_grayworld(img)
    img = apply_CLAHE(img)

    avg_rgb = np.mean(img.reshape(-1,3), axis=0).astype(int).tolist()
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

    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    h, w, _ = img.shape

    regions = {
        "心": img_lab[0:h//3, w//3:2*w//3],
        "肝": img_lab[0:h//3, 0:w//2],
        "腎": img_lab[2*h//3:h, 0:w//2],
        "脾": img_lab[2*h//3:h, w//2:w],
        "肺": img_lab[0:h//3, w//2:w]
    }

    results = {}
    for name, roi_lab in regions.items():
        avg_lab = np.mean(roi_lab.reshape(-1,3), axis=0)
        L, A, B = map(int, avg_lab)

        # 簡易中醫推論邏輯
        if A > 145 and B < 150 and L > 120:
            diagnosis = "正常"
            advice = "維持現有作息"
        elif B > 150 and A > 140 and L > 130:
            diagnosis = "偏黃，火氣旺"
            advice = "建議多喝水，避免辛辣"
        elif L > 190 and A < 135:
            diagnosis = "白苔，脾胃虛寒"
            advice = "注意保暖，飲食均衡"
        elif L < 90 and A < 130 and B < 130:
            diagnosis = "偏黑灰，腎氣不足"
            advice = "注意休息與腎臟保健"
        else:
            diagnosis = "未知"
            advice = "建議諮詢中醫師"

        results[name] = {
            "avg_lab": [L, A, B],
            "diagnosis": diagnosis,
            "advice": advice
        }

    return results

if __name__ == "__main__":
    test_image = "test.jpg"
    main_color, comment, advice, avg_rgb = analyze_image_color(test_image)
    print("Main Color:", main_color)
    print("Comment:", comment)
    print("Advice:", advice)
    print("Average RGB:", avg_rgb)

    regions = analyze_tongue_regions(test_image)
    print("Five Regions:", regions)
