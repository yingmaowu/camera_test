# app.py —— 主專案（Blueprint 版本，修正 PyMongo bool 判斷）
from flask import Flask, render_template, request, jsonify, session
import os, json, datetime, tempfile, io, base64
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
        mongo_client.admin.command("ping")  # 確認可連線
        mongo_db = mongo_client.get_database("tongueDB")
        records_collection = mongo_db.get_collection("records")
    except Exception:
        mongo_client = None
        mongo_db = None
        records_collection = None

# ---- Cloudinary ----
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("CLOUD_API_KEY"),
    api_secret=os.environ.get("CLOUD_API_SECRET")
)
# ---- 題庫（MongoDB practice_questions）----
try:
    questions_collection = mongo_db.get_collection("practice_questions") if mongo_db else None
except Exception:
    questions_collection = None
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
    # 允許 multipart file 或 base64 data（image 欄位）
    if 'image' not in request.files and 'image' not in request.form:
        return "No image uploaded", 400

    patient_id = (request.form.get('patient_id') or 'unknown').strip()
    if not patient_id:
        return "Missing patient ID", 400

    # 讀入位元資料
    image_bytes = None
    fileobj = request.files.get('image')
    if fileobj is not None:
        image_bytes = fileobj.read()
    else:
        raw = request.form.get('image', '')
        try:
            if raw.startswith('data:'):
                # data URL
                _, b64 = raw.split(',', 1)
                image_bytes = base64.b64decode(b64)
            else:
                # 純 base64
                image_bytes = base64.b64decode(raw)
        except Exception:
            return "Invalid image payload", 400

    try:
        image_stream = io.BytesIO(image_bytes)

        # 上傳至 Cloudinary（依病患分資料夾）
        up_res = cloudinary.uploader.upload(image_stream, folder=f"tongue/{patient_id}/")
        image_url = up_res.get("secure_url")

        # 暫存檔做分析
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
# 歷史紀錄
# =========================
@app.route("/history")
def history():
    patient_id = request.args.get("patient", "unknown")
    return render_template("history.html", patient_id=patient_id)

@app.route("/history_data", methods=["GET"])
def get_history_data():
    patient_id = (request.args.get("patient") or "").strip()
    if not patient_id or records_collection is None:
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
    if records_collection is None:
        return jsonify({"error": "DB 未設定"}), 500

    data = request.get_json(silent=True) or {}
    record_id = data.get("id")
    if not record_id:
        return jsonify({"error": "Missing ID"}), 400

    try:
        record = records_collection.find_one({"_id": ObjectId(record_id)})
        if record is None:
            return jsonify({"error": "Record not found"}), 404

        # 建議：上傳時把 public_id 一起存；此處以 URL 推 public_id（有子資料夾時可能不準）
        public_id = record["image_url"].split("/")[-1].split(".")[0]
        try:
            cloudinary.uploader.destroy(public_id)
        except Exception:
            pass

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
# 題庫式舌象判別練習（隨機從 Mongo/Cloudinary 出題）
# =========================
@app.get("/practice_quiz")
def practice_quiz():
    if not questions_collection:
        return "題庫未連線或未設定", 500
    try:
        q = next(questions_collection.aggregate([{"$sample": {"size": 1}}]))
    except StopIteration:
        return "題庫目前沒有題目", 404
    # 將 _id 轉為字串給表單提交使用
    qid = str(q.get("_id"))
    return render_template("practice.html", question=q, qid=qid)

@app.post("/submit_practice_answer")
def submit_practice_answer():
    if not questions_collection:
        return "題庫未連線或未設定", 500
    qid = request.form.get("qid")
    user_answer = request.form.get("answer")
    if not qid or not user_answer:
        return "缺少必要參數", 400
    try:
        q = questions_collection.find_one({"_id": ObjectId(qid)})
    except Exception:
        q = None
    if not q:
        return "找不到該題目", 404
    correct = q.get("correct_answer")
    explanation = q.get("explanation", "")
    is_correct = (user_answer == correct)
    return render_template("result.html",
                           user_answer=user_answer,
                           correct_answer=correct,
                           is_correct=is_correct,
                           explanation=explanation)
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
            r = cloudinary.api.resources(
                type="upload", resource_type="image",
                prefix=f"home/{name}", max_results=3
            )
            sample[name] = [x.get("secure_url") for x in r.get("resources", [])]
        return {"folders_under_home": folders, "samples": sample}
    except Exception as e:
        return {"error": str(e)}, 500

# =========================
# 掛載 Blueprint（新專案練習頁）
# =========================
# 確保 practice_app/__init__.py 內有 practice_bp 並定義：
#   @practice_bp.get("/")        → 練習首頁
#   @practice_bp.post("/upload") → 練習上傳分析（回傳鍵名與主專案一致）
from practice_app import practice_bp
app.register_blueprint(practice_bp, url_prefix="/practice")

# =========================
# 入口（本機啟動）
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
