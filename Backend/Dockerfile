# Use official Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Tesseract OCR for PDF processing
    tesseract-ocr \
    tesseract-ocr-eng \
    # Poppler for PDF utilities
    poppler-utils \
    # libGL for image processing (OpenCV dependencies)
    libgl1 \
    libglib2.0-0 \
    # Build tools (if needed for some Python packages)
    gcc \
    g++ \
    # Curl for health checks
    curl \
    # Clean up to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Install UV (modern Python package manager)
RUN pip install --no-cache-dir uv

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies using UV
# --system flag installs packages globally in the container
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the entire backend application
COPY Backend/ ./

# Create necessary directories for data persistence
RUN mkdir -p data/uploads data/images data/pickle data/json data/chroma_db

# Expose the port FastAPI runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
