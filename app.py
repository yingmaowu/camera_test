from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import datetime
from color_analysis import analyze_image_color  # 引入顏色分析模組（含中心區分析）

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 首頁（上傳與辨識）
@app.route("/")
def home():
    return render_template("index.html")

# 歷史頁面（可擴充用）
@app.route("/history")
def history():
    return render_template("history.html")

# 上傳圖片並辨識顏色
@app.route("/upload", methods=["POST"])
def upload_image():
    if 'image' not in request.files:
        return "No image uploaded", 400
    image = request.files['image']

    # 病人 ID（必要欄位）
    patient_id = request.form.get('patient_id', '').strip()
    if not patient_id:
        return "Missing patient ID", 400

    # 儲存圖片到 uploads/病人ID/目標圖檔.jpg
    patient_folder = os.path.join(UPLOAD_FOLDER, patient_id)
    os.makedirs(patient_folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{patient_id}_{timestamp}.jpg"
    filepath = os.path.join(patient_folder, filename)
    image.save(filepath)

    # 舌苔顏色分析（中心區平均 + RGB）
    main_color, comment, rgb = analyze_image_color(filepath)

    # 回傳分析結果
    return jsonify({
        "filename": filename,
        "舌苔主色": main_color,
        "中醫推論": comment,
        "主色RGB": rgb
    })

# 取得特定病人照片清單
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

# 提供圖片讀取
@app.route("/uploads/<patient>/<filename>")
def uploaded_file(patient, filename):
    folder = os.path.join(UPLOAD_FOLDER, patient)
    return send_from_directory(folder, filename)

# 提供所有病人清單（資料夾）
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

# 啟動應用程式（Render 用）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
