from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/capture")
def capture():
    patient_id = request.args.get("patient_id", "").strip()
    if not patient_id:
        return redirect(url_for('login'))
    return render_template("capture.html", patient_id=patient_id)

@app.route("/history")
def history():
    patient_id = request.args.get("patient_id", "").strip()
    if not patient_id:
        return redirect(url_for('login'))
    folder = os.path.join(UPLOAD_FOLDER, patient_id)
    if not os.path.exists(folder):
        os.makedirs(folder)
    files = sorted(os.listdir(folder), reverse=True)
    photos = [f"/uploads/{patient_id}/{f}" for f in files]
    return render_template("history.html", patient_id=patient_id, photos=photos)

@app.route("/upload", methods=["POST"])
def upload():
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

    return "Upload successful", 200

@app.route("/delete", methods=["POST"])
def delete():
    patient_id = request.form.get("patient_id", "").strip()
    filename = request.form.get("filename", "").strip()
    if not patient_id or not filename:
        return "Missing data", 400
    filepath = os.path.join(UPLOAD_FOLDER, patient_id, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return "Delete successful", 200
    else:
        return "File not found", 404

@app.route("/uploads/<patient_id>/<filename>")
def uploaded_file(patient_id, filename):
    folder = os.path.join(UPLOAD_FOLDER, patient_id)
    return send_from_directory(folder, filename)

if __name__ == "__main__":
    app.run(debug=True)
