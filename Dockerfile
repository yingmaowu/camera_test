# 使用完整的 python image 而非 slim
FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y         libgl1-mesa-glx         libglib2.0-0         && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 切到有 app.py 的資料夾
WORKDIR /app/camera_test-main

# 用 /bin/sh -c 才會展開 $PORT；並提供預設 8080（${PORT:-8080}）
CMD ["sh","-c","gunicorn app:app --workers 2 --threads 4 --timeout 120 --log-level debug -b 0.0.0.0:${PORT:-8080}"]
