FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Tối ưu pip: không lưu cache
ENV PIP_NO_CACHE_DIR=1

# Làm việc trong thư mục /app
WORKDIR /app

# Copy requirement trước để tận dụng cache
COPY requirements.txt .

# Cài thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source vào image
COPY . .

# Chạy FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
