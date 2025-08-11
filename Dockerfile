# 使用完整的 python image 而非 slim
FROM python:3.10

# 初始工作目錄放在 /app，稍後會切到子資料夾
WORKDIR /app

# 系統相依套件（OpenCV 需要）
RUN apt-get update && apt-get install -y         libgl1-mesa-glx         libglib2.0-0         && rm -rf /var/lib/apt/lists/*

# 安裝相依套件
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製整個專案
COPY . .

# 這行是關鍵：切到有 app.py 的資料夾
WORKDIR /app/camera_test-main

# 移除 --preload，避免啟動前初始化失敗直接退出
CMD ["gunicorn","app:app","--workers","2","--threads","4","--timeout","120","--log-level","debug","-b","0.0.0.0:${PORT}"]
