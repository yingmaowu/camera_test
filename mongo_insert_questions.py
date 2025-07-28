
import os
import random
from pymongo import MongoClient
import cloudinary
import cloudinary.api
from dotenv import load_dotenv

# 讀取環境變數
load_dotenv()
mongo_client = MongoClient(os.environ.get("MONGO_URI"))
mongo_db = mongo_client["tongueDB"]
collection = mongo_db["practice_questions"]

# Cloudinary 設定
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("CLOUD_API_KEY"),
    api_secret=os.environ.get("CLOUD_API_SECRET")
)

# 顏色分類與選項
label_choices = {
    "白苔": "白苔多見於外感風寒或虛寒體質。",
    "灰黑苔": "黑灰多見於寒濕、寒邪內盛。",
    "紅紫舌無苔": "紅舌多見於陰虛火旺或熱邪內盛。",
    "黃苔": "黃苔多見於內熱證，可能為脾胃濕熱。"
}
all_labels = list(label_choices.keys())

# 每類最多取 n 張圖片產生題目
max_images_per_type = 16
cloud_prefix = "home/"

def generate_question(label):
    try:
        result = cloudinary.api.resources(type="upload", prefix=cloud_prefix + label, max_results=max_images_per_type)
        for res in result["resources"]:
            url = res["secure_url"]
            choices = random.sample([l for l in all_labels if l != label], 3) + [label]
            random.shuffle(choices)
            doc = {
                "question": "請判斷此舌頭的主要顏色為？",
                "image_url": url,
                "choices": choices,
                "correct_answer": label,
                "explanation": label_choices[label]
            }
            collection.insert_one(doc)
            print(f"✅ 已新增題目：{label}")
    except Exception as e:
        print(f"⚠️ 無法讀取 {label}：{e}")

for label in all_labels:
    generate_question(label)
