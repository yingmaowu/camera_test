from flask import Blueprint, render_template, request, jsonify
from .practice_analysis import run_practice_analysis

practice_bp = Blueprint(
    "practice",
    __name__,
    template_folder="templates",
    static_folder="static"
)

@practice_bp.get("/")
def practice_index():
    # 練習首頁（相機預覽＋疊圖＋表單）
    return render_template("practice/index.html")

@practice_bp.post("/upload")
def practice_upload():
    """
    練習上傳分析路由：
    - 不影響主專案的 /upload
    - 回傳結構統一成主專案前端習慣的鍵名
    """
    image = request.files.get("image")
    user_answers = request.form.get("user_answers")  # JSON 字串或 None
    result = run_practice_analysis(image, user_answers)

    return jsonify({
        "舌苔主色": result.get("main_color"),
        "色彩值": result.get("avg_lab"),
        "使用者總結": result.get("summary", ""),
        "使用者觀察": result.get("answers", {}),
        "五區分析": result.get("regions", {})
    })
