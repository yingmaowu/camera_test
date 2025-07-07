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
from color_analysis import analyze_image_color, analyze_tongue_regions

load_dotenv()
app = Flask(__name__)

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

@app.route("/")
def root():
    return render_template("id.html")

@app.route("/index")
def index():
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

    try:
        image_bytes = image.read()
        image_stream = io.BytesIO(image_bytes)

        # Cloudinary 上傳
        result = cloudinary.uploader.upload(image_stream, folder=f"tongue/{patient_id}/")
        image_url = result["secure_url"]

        # 分析
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            main_color, comment, advice, rgb = analyze_image_color(tmp.name)
            five_regions = analyze_tongue_regions(tmp.name)
            os.remove(tmp.name)

        # MongoDB
        record = {
            "patient_id": patient_id,
            "image_url": image_url,
            "main_color": main_color,
            "rgb": rgb,
            "five_regions": five_regions,
            "timestamp": datetime.datetime.utcnow()
        }
        records_collection.insert_one(record)

        return jsonify({
            "image_url": image_url,
            "舌苔主色": main_color,
            "五區分析": five_regions
        })

    except Exception as e:
        return jsonify({"error": "上傳失敗", "detail": str(e)}), 500

@app.route("/history_data", methods=["GET"])
def get_history_data():
    patient_id = request.args.get("patient", "").strip()
    if not patient_id:
        return jsonify([])

    records = list(records_collection.find({"patient_id": patient_id}).sort("timestamp", -1))
    for r in records:
        r["_id"] = str(r["_id"])
    return jsonify(records)

@app.route("/delete_record", methods=["POST"])
def delete_record():
    data = request.get_json()
    record_id = data.get("id")
    if not record_id:
        return jsonify({"error": "Missing ID"}), 400

    result = records_collection.delete_one({"_id": ObjectId(record_id)})
    if result.deleted_count == 1:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Record not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
