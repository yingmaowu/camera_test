# 使用官方 Python image
FROM python:3.10-slim

# 安裝必要系統套件（新增 libgl1）
RUN apt-get update && apt-get install -y libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製需求檔與程式碼
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 開放 port
EXPOSE 8080

# 執行 Flask app
CMD ["python", "app.py"]
