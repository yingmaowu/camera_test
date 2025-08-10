# 使用完整的 python image 而非 slim
FROM python:3.10

WORKDIR /app

# 安裝系統相依套件（GL, GTK, libgthread, libglib2.0）
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# EXPOSE 非必要 on Render
CMD ["sh","-c","gunicorn app:app --workers 2 --threads 4 --timeout 120 --log-level debug --preload -b 0.0.0.0:$PORT"]

