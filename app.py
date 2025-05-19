from flask import Flask, render_template, request, jsonify
import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import tempfile
import io
from color_analysis import analyze_image_color

# 載入本地 .env 或使用 Render 的環境變數
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

# 頁面路由
@app.route("/")
def root():
    return render_template("id.html")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/history")
def history():
    return render_template("history.html")

# 上傳圖片並分析主色＋中醫推論
@app.route("/upload", methods=["POST"])
def upload_image():
    if 'image' not in request.files:
        return "No image uploaded", 400

    image = request.files['image']
    patient_id = request.form.get('patient_id', '').strip()
    if not patient_id:
        return "Missing patient ID", 400

    print(f"📸 接收到來自 {patient_id} 的圖片")

    try:
        # 先讀入 image blob，重複用於 Cloudinary 與分析
        image_bytes = image.read()
        image_stream = io.BytesIO(image_bytes)

        # 上傳到 Cloudinary
        result = cloudinary.uploader.upload(image_stream, folder=f"tongue/{patient_id}/")
        image_url = result["secure_url"]

        # 用暫存檔做 RGB 分析
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            main_color, comment, rgb = analyze_image_color(tmp.name)
            os.remove(tmp.name)

        # 存入 MongoDB
        record = {
            "patient_id": patient_id,
            "image_url": image_url,
            "main_color": main_color,
            "comment": comment,
            "rgb": rgb,
            "timestamp": datetime.datetime.utcnow()
        }
        records_collection.insert_one(record)
        print(f"✅ 已儲存影像：{image_url}")

        return jsonify({
            "image_url": image_url,
            "舌苔主色": main_color,
            "中醫推論": comment,
            "主色RGB": rgb
        })

    except Exception as e:
        print(f"❌ 上傳處理失敗：{e}")
        return jsonify({"error": "上傳失敗", "detail": str(e)}), 500

# 查詢某病患所有歷史資料
@app.route("/history_data", methods=["GET"])
def get_history_data():
    patient_id = request.args.get("patient", "").strip()
    if not patient_id:
        return jsonify([])

    try:
        records = list(records_collection.find({"patient_id": patient_id}).sort("timestamp", -1))
        for r in records:
            r["_id"] = str(r["_id"])
        print(f"📂 查詢 {patient_id} 成功，共 {len(records)} 筆")
        return jsonify(records)
    except Exception as e:
        print(f"❌ 查詢歷史紀錄錯誤：{e}")
        return jsonify({"error": "查詢失敗", "detail": str(e)}), 500

# 回傳所有病患 ID（用於 datalist）
@app.route("/patients", methods=["GET"])
def list_patients():
    try:
        patients = records_collection.distinct("patient_id")
        return jsonify(sorted(patients))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 啟動
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ MongoDB 連線成功")
    app.run(host="0.0.0.0", port=port)
