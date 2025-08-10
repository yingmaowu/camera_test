from flask import Flask, render_template, request, jsonify, session
import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import cloudinary.api  # ✅ 新增：debug 需要列資料夾/資源
import tempfile
import io
from bson import ObjectId
from color_analysis import analyze_image_color
from color_analysis_overlay import analyze_tongue_regions_with_overlay
import random

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "defaultsecret")

# MongoDB Atlas 連線
mongo_client = MongoClient(os.environ.get("MONGO_URI"))
mongo_db = mongo_client["tongueDB"]
records_collection = mongo_db["records"]

# Cloudinary 設定
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("CLOUD_API_KEY"),
    api_secret=os.environ.get("CLOUD_API_SECRET")
)

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

        # 主色與五區分析
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            tmp_path = tmp.name

        main_color, comment, advice, rgb = analyze_image_color(tmp_path)
        five_regions = analyze_tongue_regions_with_overlay(tmp_path)
        print('🧪 五區分析結果:', five_regions)

        os.remove(tmp_path)

        # 儲存紀錄至 MongoDB
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

        print(f"✅ 已儲存影像：{image_url}")

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
        print(f"❌ 上傳處理失敗：{e}")
        return jsonify({"error": "上傳失敗", "detail": str(e)}), 500

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
            public_id = record["image_url"].split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(public_id)
            records_collection.delete_one({"_id": ObjectId(record_id)})
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Record not found"}), 404
    except Exception as e:
        return jsonify({"error": "刪除失敗", "detail": str(e)}), 500

@app.route("/teaching")
def teaching():
    return render_template("teaching.html")

@app.route("/tongue_teaching")
def tongue_teaching():
    return render_template("tongue_teaching.html")

# -------------------------
# （保留原本行為）從 MongoDB 題庫出題
# -------------------------
@app.route("/practice")
def show_practice():
    question = mongo_db["practice_questions"].aggregate([{"$sample": {"size": 1}}]).next()
    session["correct_answer"] = question["correct_answer"]
    session["explanation"] = question["explanation"]
    return render_template("practice.html", question=question)

@app.route("/submit_practice_answer", methods=["POST"])
def submit_practice_answer():
    user_answer = request.form.get("answer")
    correct_answer = session.get("correct_answer")
    explanation = session.get("explanation")
    is_correct = (user_answer == correct_answer)
    return render_template("result.html", is_correct=is_correct,
                           user_answer=user_answer,
                           correct_answer=correct_answer,
                           explanation=explanation)

@app.route("/practice_zone")
def practice_zone():
    try:
        question = mongo_db["zone_questions"].aggregate([{"$sample": {"size": 1}}]).next()
    except StopIteration:
        return "No zone questions available."
    session["zone_correct"] = {
        zone: data["correct_answer"]
        for zone, data in question["zones"].items()
    }
    session["zone_explanation"] = {
        zone: data["explanation"]
        for zone, data in question["zones"].items()
    }
    return render_template("practice_zone.html", question=question)

@app.route("/submit_zone_answer", methods=["POST"])
def submit_zone_answer():
    user_answers = {k: v for k, v in request.form.items()}
    correct = session.get("zone_correct", {})
    explanation = session.get("zone_explanation", {})
    result = {
        zone: {
            "user": user_answers.get(zone),
            "correct": correct.get(zone),
            "is_correct": user_answers.get(zone) == correct.get(zone),
            "explanation": explanation.get(zone)
        }
        for zone in correct
    }
    return render_template("result_zone.html", result=result)

# -------------------------
# ✅ 新增：Debug / 健康檢查路由（不影響原行為）
# -------------------------
@app.route("/debug/routes")
def debug_routes():
    # 列出目前註冊的所有路由，確認服務是否跑到這一版
    return "<br>".join(sorted(str(r.rule) for r in app.url_map.iter_rules()))

@app.route("/debug/practice")
def debug_practice():
    # 確認 practice 系列路由活著（僅顯示文字）
    return "Practice routes are ACTIVE ✅ (current behavior: MongoDB question bank)"

@app.route("/debug/cloudinary")
def debug_cloudinary():
    # 檢視 cloudinary 的 home/ 子資料夾與每個資料夾的樣本圖片（各取最多 3 張）
    try:
        sub = cloudinary.api.sub_folders("home")  # 注意：大小寫敏感，小寫 home
        folders = [f["name"] for f in sub.get("folders", [])]
        sample = {}
        for name in folders:
            r = cloudinary.api.resources(type="upload", resource_type="image",
                                         prefix=f"home/{name}", max_results=3)
            sample[name] = [x.get("secure_url") for x in r.get("resources", [])]
        return {
            "folders_under_home": folders,
            "samples": sample
        }
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ Flask app running (original behavior preserved) + debug endpoints ready")
    app.run(host="0.0.0.0", port=port)