# 🐳 Dockerfile for FastAPI Backend

FROM python:3.10-slim-bullseye

# Install system dependencies for OpenCV and ML
RUN apt-get update --fix-missing && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY . .

# Create necessary directories
RUN mkdir -p uploads reports ml_models

# Command to run the application using Gunicorn (production)
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
