from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
import os
import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/capture")
def capture():
    patient_id = request.args.get("patient_id", "").strip()
    if not patient_id:
        return redirect(url_for('index'))
    return render_template("capture.html", patient_id=patient_id)

@app.route("/history")
def history():
    patient_id = request.args.get("patient_id", "").strip()
    if not patient_id:
        return redirect(url_for('index'))
    folder = os.path.join(UPLOAD_FOLDER, patient_id)
    photos = []
    if os.path.exists(folder):
        files = sorted(os.listdir(folder), reverse=True)
        photos = [f"/uploads/{patient_id}/{fname}" for fname in files]
    return render_template("history.html", patient_id=patient_id, photos=photos)

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

    return f"Uploaded {filename}", 200

@app.route("/delete_photo", methods=["POST"])
def delete_photo():
    patient_id = request.form.get("patient_id", "").strip()
    filename = request.form.get("filename", "").strip()
    folder = os.path.join(UPLOAD_FOLDER, patient_id)
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return redirect(url_for('history', patient_id=patient_id))
    else:
        return "File not found", 404

@app.route("/uploads/<patient>/<filename>")
def uploaded_file(patient, filename):
    folder = os.path.join(UPLOAD_FOLDER, patient)
    return send_from_directory(folder, filename)

if __name__ == "__main__":
    app.run(debug=True)
