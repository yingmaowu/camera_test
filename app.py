# app.py —— 主專案（Blueprint 版本）
from flask import Flask, render_template, request, jsonify, session
import os, uuid, json, datetime, tempfile, io
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

# MongoDB（上傳紀錄 / 歷史）
MONGO_URI = os.environ.get("MONGO_URI")
mongo_client = MongoClient(MONGO_URI) if MONGO_URI else None
mongo_db = mongo_client["tongueDB"] if mongo_client else None
records_collection = mongo_db["records"] if mongo_db else None

# Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("CLOUD_API_KEY"),
    api_secret=os.environ.get("CLOUD_API_SECRET")
)

# 健康檢查（Render/監控用）
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
    # 允許 multipart 或 base64 表單
    if 'image' not in request.files and 'image' not in request.form:
        return "No image uploaded", 400

    image = request.files.get('image') or request.form.get('image')
    patient_id = request.form.get('patient_id', 'unknown').strip()
    if not patient_id:
        return "Missing patient ID", 400

    try:
        # 讀入位元資料
        image_bytes = image.read() if hasattr(image, "read") else image
        if isinstance(image_bytes, str):
            # 若是 base64 data URL（視情況補 decode），此處僅示意
            image_bytes = image_bytes.encode("utf-8")
        image_stream = io.BytesIO(image_bytes)

        # 上傳至 Cloudinary（依病患分資料夾）
        up_res = cloudinary.uploader.upload(image_stream, folder=f"tongue/{patient_id}/")
        image_url = up_res["secure_url"]

        # 暫存檔做分析（本機短暫存檔）
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            tmp_path = tmp.name

        # 主色與五區分析（沿用你的 color_analysis* 模組）
        main_color, comment, advice, rgb = analyze_image_color(tmp_path)
        five_regions = analyze_tongue_regions_with_overlay(tmp_path)

        # 刪暫存
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        # 寫入 MongoDB（歷史紀錄）
        inserted_id = None
        if records_collection:
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
            "id": str(inserted_id) if inserted_id else None,
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
# 歷史紀錄
# =========================
@app.route("/history")
def history():
    patient_id = request.args.get("patient", "unknown")
    return render_template("history.html", patient_id=patient_id)

@app.route("/history_data", methods=["GET"])
def get_history_data():
    patient_id = request.args.get("patient", "").strip()
    if not patient_id or not records_collection:
        return jsonify([])

    try:
        records = list(records_collection.find({"patient_id": patient_id}).sort("timestamp", -1))
        for r in records:
            r["_id"] = str(r["_id"])
            r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": "查詢失敗", "detail": str(e)}), 500

@app.route("/delete_record", methods=["POST"])
def delete_record():
    if not records_collection:
        return jsonify({"error": "DB 未設定"}), 500

    data = request.get_json()
    record_id = data.get("id")
    if not record_id:
        return jsonify({"error": "Missing ID"}), 400

    try:
        record = records_collection.find_one({"_id": ObjectId(record_id)})
        if not record:
            return jsonify({"error": "Record not found"}), 404

        # 建議：上傳時把 public_id 一起存；此處以 URL 推 public_id 可能不準（有子資料夾）
        public_id = record["image_url"].split("/")[-1].split(".")[0]
        cloudinary.uploader.destroy(public_id)
        records_collection.delete_one({"_id": ObjectId(record_id)})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": "刪除失敗", "detail": str(e)}), 500

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
# Debug
# =========================
@app.route("/debug/cloudinary")
def debug_cloudinary():
    try:
        sub = cloudinary.api.subfolders("home")
        folders = [f["name"] for f in sub.get("folders", [])]
        sample = {}
        for name in folders:
            r = cloudinary.api.resources(type="upload", resource_type="image",
                                         prefix=f"home/{name}", max_results=3)
            sample[name] = [x.get("secure_url") for x in r.get("resources", [])]
        return {"folders_under_home": folders, "samples": sample}
    except Exception as e:
        return {"error": str(e)}, 500

# =========================
# 掛載 Blueprint（新專案練習頁）
# =========================
# 確保 practice_app/__init__.py 內有：
#   practice_bp = Blueprint("practice", __name__, template_folder="templates", static_folder="static")
#   @practice_bp.get("/")   → 練習首頁（相機預覽＋疊圖＋送 /practice/upload）
#   @practice_bp.post("/upload") → 練習上傳分析（結果結構與主專案一致）
from practice_app import practice_bp
app.register_blueprint(practice_bp, url_prefix="/practice")

# =========================
# 入口（本機啟動）
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
