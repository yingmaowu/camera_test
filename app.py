from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import datetime
from color_analysis import analyze_image_color

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    patient_folder = os.path.join(UPLOAD_FOLDER, patient_id)
    os.makedirs(patient_folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{patient_id}_{timestamp}.jpg"
    filepath = os.path.join(patient_folder, filename)
    image.save(filepath)

    return jsonify({"filename": filename})

@app.route("/photos", methods=["GET"])
def list_photos():
    patient_id = request.args.get("patient", "").strip()
    if not patient_id:
        return jsonify([])
    folder = os.path.join(UPLOAD_FOLDER, patient_id)
    if not os.path.exists(folder):
        return jsonify([])
    files = sorted(os.listdir(folder), reverse=True)
    urls = [f"/uploads/{patient_id}/{fname}" for fname in files]
    return jsonify(urls)

@app.route("/analyze_color")
def analyze_existing_image():
    path = request.args.get("path", "")
    if not path:
        return jsonify({"error": "Missing path"}), 400
    local_path = path.lstrip("/")
    if not os.path.exists(local_path):
        return jsonify({"error": "Image not found"}), 404

    main_color, comment, rgb = analyze_image_color(local_path)
    return jsonify({
        "舌苔主色": main_color,
        "中醫推論": comment,
        "主色RGB": rgb
    })

@app.route("/uploads/<patient>/<filename>")
def uploaded_file(patient, filename):
    folder = os.path.join(UPLOAD_FOLDER, patient)
    return send_from_directory(folder, filename)

@app.route("/patients", methods=["GET"])
def list_patients():
    try:
        folders = [
            name for name in os.listdir(UPLOAD_FOLDER)
            if os.path.isdir(os.path.join(UPLOAD_FOLDER, name))
        ]
        return jsonify(sorted(folders))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
