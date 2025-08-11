FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y         libgl1-mesa-glx         libglib2.0-0         && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 以條件切換子資料夾：若存在 camera_test-main/app.py 則進去，否則留在 /app
CMD ["sh","-c","if [ -f camera_test-main/app.py ]; then cd camera_test-main; fi; exec gunicorn app:app --workers 2 --threads 4 --timeout 120 --log-level debug -b 0.0.0.0:${PORT:-8080}"]
