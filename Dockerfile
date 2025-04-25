FROM python:3.10-slim-buster

WORKDIR /app

# 필수 빌드 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    build-essential \
    git \
    python3-dev \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:server
