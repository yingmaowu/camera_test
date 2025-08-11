# 使用完整 Python 基底
FROM python:3.10

WORKDIR /app

# OpenCV 需要的系統相依
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案所有檔案
COPY . .

# 若存在子資料夾 camera_test-main/app.py，則切進去再啟動；否則留在 /app
# 以 sh -c 形式啟動以展開 ${PORT}；未設置時預設 8080
CMD ["sh","-c","if [ -f camera_test-main/app.py ]; then cd camera_test-main; fi; exec gunicorn app:app --workers 2 --threads 4 --timeout 120 --log-level debug -b 0.0.0.0:${PORT:-8080}"]
