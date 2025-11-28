# Use Python 3.11 slim
FROM python:3.11-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libmagic-dev \
    build-essential \
    git \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install CPU-only torch and other dependencies
RUN pip install --default-timeout=300 --retries=5 --no-cache-dir \
    torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --default-timeout=300 --retries=5 --no-cache-dir -r requirements.txt --no-deps

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI with autoreload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
