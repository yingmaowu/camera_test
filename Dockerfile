# 使用官方 Python image
FROM python:3.10-slim

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
