from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.grid_overlay import overlay_grid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        if patient_id:
            session['patient_id'] = patient_id
            if 'take_photo' in request.form:
                return redirect(url_for('camera'))
            elif 'view_history' in request.form:
                return redirect(url_for('history'))
        flash("請輸入病患 ID")
    return render_template('index.html')

@app.route('/camera')
def camera():
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('index'))
    return render_template('camera.html', patient_id=patient_id)

@app.route('/upload', methods=['POST'])
def upload():
    patient_id = session.get('patient_id')
    if 'photo' not in request.files or not patient_id:
        return redirect(url_for('camera'))

    file = request.files['photo']
    if file.filename == '':
        return redirect(url_for('camera'))

    filename = secure_filename(datetime.now().strftime(f"{patient_id}_%Y%m%d_%H%M%S.jpg"))
    patient_dir = os.path.join(app.config['UPLOAD_FOLDER'], patient_id)
    os.makedirs(patient_dir, exist_ok=True)
    file_path = os.path.join(patient_dir, filename)
    file.save(file_path)

    # 套用九宮格疊圖
    overlay_grid(file_path)

    # TODO: 加入舌苔辨識模型

    return redirect(url_for('history'))

@app.route('/history')
def history():
    patient_id = session.get('patient_id')
    if not patient_id:
        return redirect(url_for('index'))

    patient_dir = os.path.join(app.config['UPLOAD_FOLDER'], patient_id)
    photos = os.listdir(patient_dir) if os.path.exists(patient_dir) else []
    photos.sort(reverse=True)
    return render_template('history.html', patient_id=patient_id, photos=photos)

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    patient_id = session.get('patient_id')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], patient_id, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('history'))

@app.route('/uploads/<patient_id>/<filename>')
def uploaded_file(patient_id, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], patient_id), filename)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
