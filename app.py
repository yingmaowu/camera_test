from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return redirect(url_for('patient'))

@app.route('/patient')
def patient():
    return render_template('patient.html')

@app.route('/camera')
def camera():
    patient_id = request.args.get('patient_id')
    return render_template('index.html', patient_id=patient_id)

@app.route('/history')
def history():
    patient_id = request.args.get('patient_id')
    return render_template('history.html', patient_id=patient_id)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
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

    return f"Uploaded {filename}", 200

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

@app.route("/admin")
def admin_page():
    patients = []
    for name in os.listdir(UPLOAD_FOLDER):
        folder_path = os.path.join(UPLOAD_FOLDER, name)
        if os.path.isdir(folder_path):
            files = sorted(os.listdir(folder_path), reverse=True)
            photos = [f"/uploads/{name}/{f}" for f in files]
            patients.append({
                "id": name,
                "count": len(photos),
                "photos": photos
            })
    return render_template("admin.html", patients=patients)

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/validate_patient", methods=["POST"])
def validate_patient():
    patient_id = request.form.get("patient_id", "").strip()
    if not patient_id:
        return "Missing ID", 400

    patient_folder = os.path.join(UPLOAD_FOLDER, patient_id)
    created = False
    if not os.path.exists(patient_folder):
        os.makedirs(patient_folder)
        created = True

    return jsonify({
        "patient_id": patient_id,
        "created": created
    })

@app.route("/dashboard")
def dashboard():
    patient_id = request.args.get("patient", "").strip()
    return render_template("dashboard.html", patient=patient_id)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
