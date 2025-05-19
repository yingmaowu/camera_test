from flask import Flask, render_template, request, jsonify
import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import tempfile
from color_analysis import analyze_image_color

# 載入 .env 檔案
load_dotenv()

app = Flask(__name__)

# MongoDB Atlas 連線
try:
    mongo_client = MongoClient(os.environ.get("MONGO_URI"), serverSelectionTimeoutMS=5000)
    mongo_db = mongo_client["tongueDB"]
    records_collection = mongo_db["records"]
    print("✅ MongoDB 連線成功")
except Exception as e:
    print(f"❌ MongoDB 連線失敗：{e}")
    records_collection = None

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
    try:
        if 'image' not in request.files:
            return "No image uploaded", 400
        image = request.files['image']
        patient_id = request.form.get('patient_id', '').strip()
        if not patient_id:
            return "Missing patient ID", 400

        print(f"📸 接收到來自 {patient_id} 的圖片")

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

        if records_collection:
            insert_result = records_collection.insert_one(record)
            print("✅ 成功寫入 MongoDB：", insert_result.inserted_id)
        else:
            print("❌ 無法寫入 MongoDB，records_collection 是 None")

        return jsonify({
            "image_url": image_url,
            "舌苔主色": main_color,
            "中醫推論": comment,
            "主色RGB": rgb
        })

    except Exception as e:
        print(f"❌ 上傳處理失敗：{e}")
        return jsonify({"error": str(e)}), 500

@app.route("/history_data", methods=["GET"])
def get_history_data():
    try:
        patient_id = request.args.get("patient", "").strip()
        if not patient_id:
            return jsonify([])

        if not records_collection:
            return jsonify({"error": "MongoDB 未連接"}), 500

        records = list(records_collection.find({"patient_id": patient_id}).sort("timestamp", -1))
        for r in records:
            r["_id"] = str(r["_id"])
        print(f"📚 查詢 {patient_id} 歷史紀錄，共 {len(records)} 筆")
        return jsonify(records)

    except Exception as e:
        print(f"❌ 查詢歷史紀錄錯誤：{e}")
        return jsonify({"error": str(e)}), 500

@app.route("/patients", methods=["GET"])
def list_patients():
    try:
        if not records_collection:
            return jsonify([])

        patients = records_collection.distinct("patient_id")
        print(f"👤 當前所有病患 ID：{patients}")
        return jsonify(sorted(patients))

    except Exception as e:
        print(f"❌ 取得病患清單錯誤：{e}")
        return jsonify([])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
