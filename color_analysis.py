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
    if np.sum(mask > 0) < 100:
        return "未知", "舌頭面積過小", "請重新拍攝", (0,0,0)

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    masked_lab_pixels = lab[mask > 0]
    avg_lab = np.mean(masked_lab_pixels, axis=0)
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

    return comment, "中醫推論: " + comment, "請依中醫師建議調理", (L,A,B)

def analyze_five_regions(image_path):
    img = cv2.imread(image_path)
    img = apply_grayworld(img)
    img = apply_CLAHE(img)

    mask = extract_tongue_mask(img)
    if np.sum(mask > 0) < 100:
        print("⚠️ 舌頭有效面積過小")
        return {"error": "舌頭面積過小"}

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    h, w = mask.shape

    regions = {
        "心肺": mask[0:h//3, w//3:2*w//3],
        "脾胃": mask[h//3:2*h//3, w//3:2*w//3],
        "肝": mask[h//3:2*h//3, 0:w//3],
        "膽": mask[h//3:2*h//3, 2*w//3:w],
        "腎": mask[2*h//3:h, w//3:2*w//3],
    }

    results = {}
    for name, region_mask in regions.items():
        region_lab = lab[
            (region_mask > 0).nonzero()[0] + (lab.shape[0] - region_mask.shape[0]),
            (region_mask > 0).nonzero()[1] + (lab.shape[1] - region_mask.shape[1])
        ] if np.sum(region_mask > 0) > 0 else np.array([[0,0,0]])

        avg_lab = np.mean(region_lab, axis=0) if len(region_lab) > 0 else [0,0,0]
        L, A, B = map(int, avg_lab)

        print(f"{name}區: L={L}, A={A}, B={B}")

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

        results[name] = {"L": L, "A": A, "B": B, "推論": comment}

    return results
