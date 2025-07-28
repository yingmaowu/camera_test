from flask import Flask, render_template, request, jsonify
import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import tempfile
import io
from bson import ObjectId
from color_analysis import analyze_image_color
from color_analysis_overlay import analyze_tongue_regions_with_overlay

load_dotenv()
app = Flask(__name__)

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

        # 進行主色與五區分析
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            tmp_path = tmp.name

        main_color, comment, advice, rgb = analyze_image_color(tmp_path)
        five_regions = analyze_tongue_regions_with_overlay(tmp_path)
        print('🧪 五區分析結果:', five_regions)

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ Flask app running with integrated tongue color and region analysis.")
    app.run(host="0.0.0.0", port=port)
@app.route("/teaching")
def teaching():
    return render_template("teaching.html")

@app.route("/tongue_teaching")
def tongue_teaching():
    return render_template("tongue_teaching.html")
