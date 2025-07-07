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
        result = cloudinary.uploader.upload(image_stream, folder=f"tongue/{patient_id}/")
        image_url = result["secure_url"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            main_color, comment, advice, rgb = analyze_image_color(tmp.name)
            five_regions = analyze_five_regions(tmp.name)
            os.remove(tmp.name)

        debug_info = { region: five_regions[region] for region in five_regions }

        record = {
            "patient_id": patient_id,
            "image_url": image_url,
            "main_color": main_color,
            "comment": comment,
            "advice": advice,
            "rgb": rgb,
            "five_regions": five_regions,
            "debug": debug_info,
            "timestamp": datetime.datetime.utcnow()
        }
        records_collection.insert_one(record)

        return jsonify({
            "image_url": image_url,
            "舌苔主色": main_color,
            "中醫推論": comment,
            "醫療建議": advice,
            "主色RGB": rgb,
            "五區分析": five_regions,
            "debug": debug_info
        })
    except Exception as e:
        return jsonify({"error": "上傳失敗", "detail": str(e)}), 500
