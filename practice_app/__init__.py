from flask import Blueprint, render_template, request, jsonify
from .practice_analysis import run_practice_analysis  # 你的新專案分析入口

practice_bp = Blueprint(
    "practice",
    __name__,
    template_folder="templates",
    static_folder="static"
)

@practice_bp.get("/")
def practice_index():
    return render_template("practice/index.html")

@practice_bp.post("/upload")
def practice_upload():
    image = request.files.get("image")
    user_answers = request.form.get("user_answers")
    result = run_practice_analysis(image, user_answers)

    # 若新專案回傳格式不同，這裡轉成主專案慣用的形狀
    return jsonify({
        "舌苔主色": result.get("main_color"),
        "色彩值": result.get("avg_lab"),
        "使用者總結": result.get("summary", ""),
        "使用者觀察": result.get("answers", {}),
        "五區分析": result.get("regions", {})
    })

