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

def extract_tongue_mask(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    return cv2.bitwise_or(mask1, mask2)

def analyze_image_color(image_path):
    img = cv2.imread(image_path)
    img = apply_grayworld(img)
    img = apply_CLAHE(img)

    mask = extract_tongue_mask(img)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    tongue_lab = lab[mask > 0]

    if len(tongue_lab) < 100:
        return "未知", "無法判斷", "請重新拍攝更清晰且光線正常的圖片", (0,0,0)

    avg_lab = np.mean(tongue_lab, axis=0)
    L, A, B = map(int, avg_lab)

    if A > 145 and B < 150 and L > 120:
        comment = "正常舌色"
    elif B > 150 and A > 140 and L > 130:
        comment = "偏黃，火氣較旺"
    elif L > 190 and A < 135:
        comment = "白苔，脾胃虛寒"
    elif L < 90 and A < 130 and B < 130:
        comment = "偏黑灰，腎氣不足"
    else:
        comment = "未知"

    return comment, comment, "請保持健康生活習慣", (L,A,B)

def analyze_five_regions(image_path):
    img = cv2.imread(image_path)
    img = apply_grayworld(img)
    img = apply_CLAHE(img)

    mask = extract_tongue_mask(img)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    h, w, _ = img.shape

    regions = {
        "心肺": lab[int(h*0.8):h, int(w*0.25):int(w*0.75)],
        "肝": lab[int(h*0.4):int(h*0.7), 0:int(w*0.3)],
        "脾胃": lab[int(h*0.4):int(h*0.7), int(w*0.3):int(w*0.7)],
        "腎": lab[0:int(h*0.3), int(w*0.3):int(w*0.7)],
        "膽": lab[int(h*0.4):int(h*0.7), int(w*0.7):w],
    }

    results = {}
    for name, region_lab in regions.items():
        if len(region_lab) < 10:
            results[name] = {"L":0, "A":0, "B":0, "推論":"無法判斷"}
            continue
        avg_lab = np.mean(region_lab, axis=(0,1))
        L, A, B = map(int, avg_lab)
        if A > 145 and B < 150 and L > 120:
            comment = "正常舌色"
        elif B > 150 and A > 140 and L > 130:
            comment = "偏黃"
        elif L > 190 and A < 135:
            comment = "白苔"
        elif L < 90 and A < 130 and B < 130:
            comment = "偏黑灰"
        else:
            comment = "無法判斷"
        results[name] = {"L":L, "A":A, "B":B, "推論":comment}

    return results
