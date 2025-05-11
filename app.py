from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
import os
import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 首頁登入頁：輸入病患 ID 並選擇功能
@app.route("/")
def login_page():
    return render_template("login.html")

# 驗證病患 ID，並依照動作導入拍攝或歷史查詢
@app.route("/validate_patient", methods=["POST"])
def validate_patient():
    patient_id = request.form.get("patient_id", "").strip()
    action = request.form.get("action", "")
    if not patient_id:
        return "Missing ID", 400

    patient_folder = os.path.join(UPLOAD_FOLDER, patient_id)
    created = False
    if not os.path.exists(patient_folder):
        os.makedirs(patient_folder)
        created = True

    # 根據按鈕選擇導入不同頁面
    if action == "capture":
        return redirect(url_for("capture_page", patient=patient_id))
    elif action == "history":
        return redirect(url_for("history", patient=patient_id))
    else:
        return "Invalid action", 400

# 拍照頁
@app.route("/capture")
def capture_page():
    patient_id = request.args.get("patient", "").strip()
    return render_template("capture.html", patient=patient_id)

# 歷史照片頁
@app.route("/history")
def history():
    patient_id = request.args.get("patient", "").strip()
    return render_template("history.html", patient=patient_id)

# 選單頁（可選拍照／歷史／返回首頁）
@app.route("/dashboard")
def dashboard():
    patient_id = request.args.get("patient", "").strip()
    return render_template("dashboard.html", patient=patient_id)

# 圖片上傳 API
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

# 列出某病患歷史照片
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

# 顯示圖片檔案
@app.route("/uploads/<patient>/<filename>")
def uploaded_file(patient, filename):
    folder = os.path.join(UPLOAD_FOLDER, patient)
    return send_from_directory(folder, filename)

# 所有病患清單（給 datalist 用）
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
