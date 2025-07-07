from flask import Flask, render_template, request, jsonify
import os, datetime, io, tempfile
from dotenv import load_dotenv
from pymongo import MongoClient
import cloudinary, cloudinary.uploader
from bson import ObjectId
from color_analysis import analyze_image_color, analyze_five_regions

load_dotenv()
app = Flask(__name__)

# MongoDB Atlas
mongo_client = MongoClient(os.environ["MONGO_URI"])
db = mongo_client["tongueDB"]
col = db["records"]

# Cloudinary
cloudinary.config(
    cloud_name=os.environ["CLOUD_NAME"],
    api_key=os.environ["CLOUD_API_KEY"],
    api_secret=os.environ["CLOUD_API_SECRET"]
)

@app.route("/")
def root(): return render_template("id.html")

@app.route("/index")
def index(): return render_template("index.html")

@app.route("/history")
def history(): return render_template("history.html")

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'image' not in request.files:
        return "No image uploaded", 400

    img = request.files['image']
    pid = request.form.get('patient_id', '').strip()
    if not pid:
        return "Missing patient ID", 400

    b = img.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(b); tmp.flush()

    main_color, comment, advice, debug = analyze_image_color(tmp.name)
    five_regions = analyze_five_regions(tmp.name)
    tmp.close(); os.remove(tmp.name)

    url = cloudinary.uploader.upload(io.BytesIO(b), folder=f"tongue/{pid}/")["secure_url"]
    rec = {
        "patient_id": pid,
        "image_url": url,
        "main_color": main_color,
        "comment": comment,
        "advice": advice,
        "debug": debug,
        "five_regions": five_regions,
        "timestamp": datetime.datetime.utcnow()
    }
    col.insert_one(rec)
    return jsonify({"舌苔主色": main_color, "推論": comment, "建議": advice, "debug": debug, "五區": five_regions})

@app.route("/history_data")
def history_data():
    pid = request.args.get("patient", "").strip()
    rs = list(col.find({"patient_id": pid}).sort("timestamp", -1))
    for r in rs: r["_id"] = str(r["_id"])
    return jsonify(rs)

@app.route("/delete_record", methods=["POST"])
def delete_record():
    rid = request.get_json().get("id")
    col.delete_one({"_id": ObjectId(rid)})
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
