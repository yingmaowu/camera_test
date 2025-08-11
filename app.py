from flask import Flask, render_template, request, jsonify
import os, json, datetime, tempfile, io, base64, random

from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

import cloudinary
import cloudinary.uploader
import cloudinary.api

from color_analysis import analyze_image_color
from color_analysis_overlay import analyze_tongue_regions_with_overlay

# =========================
# 基本設定
# =========================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "defaultsecret")

# ---- MongoDB（上傳紀錄 / 歷史）----
MONGO_URI = os.environ.get("MONGO_URI")
mongo_client = None
mongo_db = None
records_collection = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI)
        mongo_client.admin.command("ping")
        mongo_db = mongo_client.get_database("tongueDB")
        records_collection = mongo_db.get_collection("records")
    except Exception:
        mongo_client = None
        mongo_db = None
        records_collection = None

# ---- Cloudinary（支援 CLOUDINARY_URL 或三鍵）----
cloudinary_url = os.environ.get("CLOUDINARY_URL")
if cloudinary_url:
    cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
else:
    cloudinary.config(
        cloud_name=os.environ.get("CLOUD_NAME"),
        api_key=os.environ.get("CLOUD_API_KEY"),
        api_secret=os.environ.get("CLOUD_API_SECRET"),
        secure=True,
    )

# =========================
# Cloudinary 直接出題（核心版行為）
# =========================
LABEL_EXPLANATION = {
    "白苔": "白苔多見於外感風寒或虛寒體質。",
    "黃苔": "黃苔多見於內熱證，可能為脾胃濕熱。",
    "灰黑苔": "黑灰多見於寒濕、寒邪內盛。",
    "紅紫舌無苔": "紅舌多見於陰虛火旺或熱邪內盛。",
}

def get_labels_from_cloud(base_folder: str):
    # 讀取 home/ 下的子資料夾名稱作為標籤；若抓不到就用預設四類
    try:
        sub = cloudinary.api.subfolders(base_folder)
        labels = [f["name"] for f in sub.get("folders", [])]
        if labels:
            return labels
    except Exception:
        pass
    return ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

def pick_cloud_question(base_folder: str):
    labels = get_labels_from_cloud(base_folder)

    # 僅使用「有圖片」的資料夾
    non_empty = []
    for lb in labels:
        r = cloudinary.api.resources(
            type="upload", resource_type="image",
            prefix=f"{base_folder}/{lb}/", max_results=1
        )
        if r.get("resources"):
            non_empty.append(lb)
    if not non_empty:
        raise RuntimeError(f"{base_folder} 底下沒有可用圖片（labels={labels}）")

    correct = random.choice(non_empty)
    r = cloudinary.api.resources(
        type="upload", resource_type="image",
        prefix=f"{base_folder}/{correct}/", max_results=200
    )
    res = r.get("resources", [])
    if not res:
        raise RuntimeError(f"{base_folder}/{correct} 沒有圖片")

    url = random.choice(res).get("secure_url")

    others = [l for l in labels if l != correct]
    k = min(3, len(others))
    choices = random.sample(others, k=k) + [correct]
    random.shuffle(choices)

    return {
        "question": "請判斷此舌頭的主要顏色為？",
        "image_url": url,
        "choices": choices,
        "correct_answer": correct,
        "explanation": LABEL_EXPLANATION.get(correct, correct),
    }

# 健康檢查
@app.get("/healthz")
def healthz():
    return "ok", 200

# =========================
# 一般頁面
# =========================
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/id")
def id_input():
    next_page = request.args.get("next", "index")
    return render_template("id.html", next_page=next_page)

@app.route("/index")
def index():
    patient_id = request.args.get("patient", "unknown")
    return render_template("index.html", patient_id=patient_id)

# =========================
# 上傳、分析、儲存（主流程）
# =========================
@app.route("/upload", methods=["POST"])
def upload_image():
    if 'image' not in request.files and 'image' not in request.form:
        return "No image uploaded", 400

    patient_id = (request.form.get('patient_id') or 'unknown').strip()
    if not patient_id:
        return "Missing patient ID", 400

    image_bytes = None
    fileobj = request.files.get('image')
    if fileobj is not None:
        image_bytes = fileobj.read()
    else:
        raw = request.form.get('image', '')
        try:
            if raw.startswith('data:'):
                _, b64 = raw.split(',', 1)
                image_bytes = base64.b64decode(b64)
            else:
                image_bytes = base64.b64decode(raw)
        except Exception:
            return "Invalid image payload", 400

    try:
        image_stream = io.BytesIO(image_bytes)
        up_res = cloudinary.uploader.upload(image_stream, folder=f"tongue/{patient_id}/")
        image_url = up_res.get("secure_url")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            tmp_path = tmp.name

        main_color, comment, advice, rgb = analyze_image_color(tmp_path)
        five_regions = analyze_tongue_regions_with_overlay(tmp_path)

        try:
            os.remove(tmp_path)
        except Exception:
            pass

        inserted_id = None
        if records_collection is not None:
            record = {
                "patient_id": patient_id,
                "image_url": image_url,
                "main_color": main_color,
                "comment": comment,
                "advice": advice,
                "rgb": rgb,
                "five_regions": five_regions,
                "timestamp": datetime.datetime.utcnow()
            }
            inserted_id = records_collection.insert_one(record).inserted_id

        return jsonify({
            "success": True,
            "id": str(inserted_id) if inserted_id is not None else None,
            "image_url": image_url,
            "舌苔主色": main_color,
            "中醫推論": comment,
            "醫療建議": advice,
            "主色RGB": rgb,
            "五區分析": five_regions
        })
    except Exception as e:
        return jsonify({"error": "上傳失敗", "detail": str(e)}), 500

# =========================
# 教學頁
# =========================
@app.route("/teaching")
def teaching():
    return render_template("teaching.html")

@app.route("/tongue_teaching")
def tongue_teaching():
    return render_template("tongue_teaching.html")

# =========================
# 舌象判別練習（核心版：Cloudinary 直接出題）
# =========================
@app.get("/practice_quiz")
def practice_quiz():
    base_folder = os.environ.get("CLOUD_SOURCE_FOLDER", "home")
    try:
        q = pick_cloud_question(base_folder)
        return render_template("practice.html", question=q, qid=None, correct=q["correct_answer"])
    except Exception as e:
        return f"無法從 Cloudinary 取題：{e}", 500

@app.post("/submit_practice_answer")
def submit_practice_answer():
    user_answer = request.form.get("answer")
    correct = request.form.get("correct")
    if not user_answer or not correct:
        return "缺少必要參數", 400
    explanation = LABEL_EXPLANATION.get(correct, "")
    is_correct = (user_answer == correct)
    return render_template("result.html",
                           user_answer=user_answer,
                           correct_answer=correct,
                           is_correct=is_correct,
                           explanation=explanation)

# =========================
# Debug（查看 Cloudinary 子資料夾與樣本）
# =========================
@app.route("/debug/cloudinary")
def debug_cloudinary():
    try:
        base_folder = os.environ.get("CLOUD_SOURCE_FOLDER", "home")
        sub = cloudinary.api.subfolders(base_folder)
        folders = [f["name"] for f in sub.get("folders", [])]
        sample = {}
        for name in folders:
            r = cloudinary.api.resources(
                type="upload", resource_type="image",
                prefix=f"{base_folder}/{name}/", max_results=3
            )
            sample[name] = [x.get("secure_url") for x in r.get("resources", [])]
        return {"base_folder": base_folder, "folders": folders, "samples": sample}
    except Exception as e:
        return {"error": str(e)}, 500

# =========================
# 掛載 Blueprint（中醫五區辨識練習，原樣保留）
# =========================
from practice_app import practice_bp
app.register_blueprint(practice_bp, url_prefix="/practice")

# =========================
# 入口（本機啟動）
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
