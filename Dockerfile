FROM python:3.10

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -o Acquire::Retries=3 && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
