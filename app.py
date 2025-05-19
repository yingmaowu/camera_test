from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import tempfile
from color_analysis import analyze_image_color

# 載入本地 .env 或使用 Render 的環境變數
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
def root():
    return render_template("id.html")

@app.route("/index")
def home():
    return render_template("index.html")

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'image' not in request.files:
        return "No image uploaded", 400
    image = request.files['image']
    patient_id = request.form.get('patient_id', '').strip()
    if not patient_id:
        return "Missing patient ID", 400

    # 上傳圖片到 Cloudinary
    result = cloudinary.uploader.upload(image, folder=f"tongue/{patient_id}/")
    image_url = result["secure_url"]

    # 使用暫存檔分析顏色
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        image.save(tmp.name)
        main_color, comment, rgb = analyze_image_color(tmp.name)
        os.remove(tmp.name)

    # 儲存紀錄到 MongoDB
    record = {
        "patient_id": patient_id,
        "image_url": image_url,
        "main_color": main_color,
        "comment": comment,
        "rgb": rgb,
        "timestamp": datetime.datetime.utcnow()
    }
    records_collection.insert_one(record)

    return jsonify({
        "image_url": image_url,
        "舌苔主色": main_color,
        "中醫推論": comment,
        "主色RGB": rgb
    })

@app.route("/history_data", methods=["GET"])
def get_history_data():
    patient_id = request.args.get("patient", "").strip()
    if not patient_id:
        return jsonify([])

    records = list(records_collection.find({"patient_id": patient_id}).sort("timestamp", -1))
    for r in records:
        r["_id"] = str(r["_id"])
    return jsonify(records)

@app.route("/patients", methods=["GET"])
def list_patients():
    patients = records_collection.distinct("patient_id")
    return jsonify(sorted(patients))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
