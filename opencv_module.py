import cv2
import numpy as np
import os

def analyze_image_with_visual_feedback(image_path, debug_save_path=None):
    """
    僅針對中央九宮格區域（中間 1/3）做紅色遮罩與偵測。
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
    h, w = image_resized.shape[:2]

    # 只分析中央九宮格 1/3x1/3 區域
    x_start = w // 3
    y_start = h // 3
    x_end = x_start * 2
    y_end = y_start * 2
    central_roi = image_resized[y_start:y_end, x_start:x_end]

    hsv = cv2.cvtColor(central_roi, cv2.COLOR_BGR2HSV)

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
        x, y, w_box, h_box = cv2.boundingRect(largest)

        # 調整回整張圖座標系
        x_full = x + x_start
        y_full = y + y_start

        tongue_crop = image_resized[y_full:y_full + h_box, x_full:x_full + w_box]
        avg_color = cv2.mean(tongue_crop)[:3]
        avg_rgb = tuple(int(c) for c in avg_color[::-1])  # BGR → RGB

        cv2.rectangle(image_resized, (x_full, y_full), (x_full + w_box, y_full + h_box), (0, 255, 0), 2)

        if debug_save_path:
            os.makedirs(os.path.dirname(debug_save_path), exist_ok=True)
            cv2.imwrite(debug_save_path, image_resized)

        return {
            "tongue_rgb": avg_rgb,
            "cropped_shape": tongue_crop.shape,
            "bounding_box": (x_full, y_full, w_box, h_box)
        }

    else:
        return {
            "tongue_rgb": None,
            "cropped_shape": None,
            "bounding_box": None,
            "error": "無法偵測舌頭區域"
        }
