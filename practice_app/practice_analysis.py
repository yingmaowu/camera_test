import os, uuid, json
from werkzeug.datastructures import FileStorage

# 重用主專案的分析模組（保持一致）
from color_analysis import analyze_image_color, analyze_tongue_regions

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def run_practice_analysis(image_file: FileStorage, user_answers_json: str | None):
    if not image_file:
        return {"error": "No image uploaded"}

    # 儲存上傳圖片（與主專案一致的行為）
    filename = f"practice_{uuid.uuid4().hex}.jpg"
    path = os.path.join(UPLOAD_DIR, filename)
    image_file.save(path)

    # 主色 + 五區分析（沿用主專案邏輯）
    main_color, _, _, avg_lab = analyze_image_color(path)
    regions = analyze_tongue_regions(path)

    # 解析使用者觀察
    try:
        user_answers = json.loads(user_answers_json) if user_answers_json else {}
    except json.JSONDecodeError:
        user_answers = {}

    return {
        "main_color": main_color,
        "avg_lab": avg_lab,
        "answers": user_answers,
        "regions": regions,
        "summary": ""  # 前端會帶 user_summary 時再補
    }
