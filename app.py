from flask import Flask, render_template, request, jsonify, session
import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import cloudinary.api
import tempfile
import io
from bson import ObjectId
from color_analysis import analyze_image_color
from color_analysis_overlay import analyze_tongue_regions_with_overlay
import random

# -------------------------
# 基本設定
# -------------------------
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "defaultsecret")

# MongoDB Atlas
mongo_client = MongoClient(os.environ.get("MONGO_URI"))
mongo_db = mongo_client["tongueDB"]
records_collection = mongo_db["records"]

# Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("CLOUD_API_KEY"),
    api_secret=os.environ.get("CLOUD_API_SECRET")
)

# -------------------------
# 一般頁面
# -------------------------
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

# -------------------------
# 上傳、分析、儲存
# -------------------------
@app.route("/upload", methods=["POST"])
def upload_image():
    if 'image' not in request.files and 'image' not in request.form:
        return "No image uploaded", 400

    image = request.files.get('image') or request.form.get('image')
    patient_id = request.form.get('patient_id', 'unknown').strip()

    if not patient_id:
        return "Missing patient ID", 400

    print(f"📸 接收到來自 {patient_id} 的圖片")

    try:
        image_bytes = image.read()
        image_stream = io.BytesIO(image_bytes)

        # 上傳至 Cloudinary
        result = cloudinary.uploader.upload(image_stream, folder=f"tongue/{patient_id}/")
        image_url = result["secure_url"]
        print(f"☁️ Cloudinary 上傳成功：{image_url}")

        # 暫存檔供分析
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            tmp_path = tmp.name

        # 主色與五區分析
        main_color, comment, advice, rgb = analyze_image_color(tmp_path)
        five_regions = analyze_tongue_regions_with_overlay(tmp_path)
        print("🧪 五區分析結果:", five_regions)

        # 移除暫存檔
        os.remove(tmp_path)

        # 寫入 MongoDB
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
        print(f"✅ 紀錄已寫入 MongoDB：{inserted_id}")

        return jsonify({
            "success": True,
            "id": str(inserted_id),
            "image_url": image_url,
            "舌苔主色": main_color,
            "中醫推論": comment,
            "醫療建議": advice,
            "主色RGB": rgb,
            "五區分析": five_regions
        })

    except Exception as e:
        print(f"❌ 上傳或分析失敗：{e}")
        return jsonify({"error": "上傳失敗", "detail": str(e)}), 500

# -------------------------
# 歷史紀錄
# -------------------------
@app.route("/history")
def history():
    patient_id = request.args.get("patient", "unknown")
    return render_template("history.html", patient_id=patient_id)

@app.route("/history_data", methods=["GET"])
def get_history_data():
    patient_id = request.args.get("patient", "").strip()
    if not patient_id:
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
    data = request.get_json()
    record_id = data.get("id")
    if not record_id:
        return jsonify({"error": "Missing ID"}), 400

    try:
        record = records_collection.find_one({"_id": ObjectId(record_id)})
        if record:
            # 若需要完整 public_id，建議儲存時順便存 public_id；這裡先做簡化處理
            public_id = record["image_url"].split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(public_id)
            records_collection.delete_one({"_id": ObjectId(record_id)})
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Record not found"}), 404
    except Exception as e:
        return jsonify({"error": "刪除失敗", "detail": str(e)}), 500

# -------------------------
# 教學頁
# -------------------------
@app.route("/teaching")
def teaching():
    return render_template("teaching.html")

@app.route("/tongue_teaching")
def tongue_teaching():
    return render_template("tongue_teaching.html")

# -------------------------
# Cloudinary 隨機出題（關鍵）
# -------------------------
@app.route("/practice")
def practice():
    print("🟣 [practice] Cloudinary 出題路由已被呼叫")

    labels = {
        "white": "白苔",
        "black": "灰黑苔",
        "red": "紅紫舌無苔",
        "yellow": "黃苔"
    }

    questions = []
    counts = {}
    try:
        for folder, label in labels.items():
            res = cloudinary.api.resources(
                type="upload",
                prefix=f"home/{label}",   # 確認你的 Cloudinary 目錄為 home/白苔 等
                max_results=100
            )
            cnt = len(res.get("resources", []))
            counts[label] = cnt
            if cnt > 0:
                questions.append({
                    "url": random.choice(res["resources"])["secure_url"],
                    "label": label
                })
    except Exception as e:
        print(f"❌ Cloudinary 錯誤：{e}")
        return f"❌ Cloudinary 錯誤：{e}"

    print(f"🟣 [practice] 取圖統計：{counts}")

    if not questions:
        return "⚠️ Cloudinary 沒有可用圖片（請確認 home/白苔、home/灰黑苔、home/紅紫舌無苔、home/黃苔）"

    q = random.choice(questions)
    choices = list(labels.values())
    random.shuffle(choices)

    session["answer"] = q["label"]
    return render_template("practice.html", question={
        "image_url": q["url"],
        "question": "這是哪一種舌象？",
        "choices": choices
    })

@app.route("/submit_practice_answer", methods=["POST"])
def submit_practice_answer():
    user_answer = request.form.get("answer")
    correct_answer = session.get("answer")
    is_correct = (user_answer == correct_answer)
    explanation = f"這張圖的分類是：{correct_answer}，請注意舌苔顏色與質地的差異。"

    return render_template("result.html",
                           user_answer=user_answer,
                           correct_answer=correct_answer,
                           is_correct=is_correct,
                           explanation=explanation)

# -------------------------
# 健康檢查／確認來源
# -------------------------
@app.route("/debug/practice")
def debug_practice():
    return "Cloudinary practice route is ACTIVE ✅"

# -------------------------
# 入口
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ Flask app running with Cloudinary-based practice + MongoDB records")
    app.run(host="0.0.0.0", port=port)
