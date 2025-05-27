import cv2
import numpy as np
import os

def analyze_image_with_visual_feedback(image_path, debug_save_path=None):
    """
    利用 OpenCV 分析紅色區域並框出可能的舌頭區塊，並可將視覺化圖儲存。
    """
    image = cv2.imread(image_path)
    if image is None:
        return {
            "tongue_rgb": None,
            "cropped_shape": None,
            "bounding_box": None,
            "error": "無法讀取圖片"
        }

    image_resized = cv2.resize(image, (300, 300))
    hsv = cv2.cvtColor(image_resized, cv2.COLOR_BGR2HSV)

    # 紅色遮罩
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([179, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        tongue_crop = image_resized[y:y+h, x:x+w]
        avg_color = cv2.mean(tongue_crop)[:3]
        avg_rgb = tuple(int(c) for c in avg_color[::-1])  # BGR to RGB

        cv2.rectangle(image_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if debug_save_path:
            os.makedirs(os.path.dirname(debug_save_path), exist_ok=True)
            cv2.imwrite(debug_save_path, image_resized)

        return {
            "tongue_rgb": avg_rgb,
            "cropped_shape": tongue_crop.shape,
            "bounding_box": (x, y, w, h)
        }
    else:
        return {
            "tongue_rgb": None,
            "cropped_shape": None,
            "bounding_box": None,
            "error": "無法偵測舌頭區域"
        }
