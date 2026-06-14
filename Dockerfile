FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (BuildKit cache for faster rebuilds)
# Install CPU PyTorch first (lightweight, ~250MB total instead of ~6GB CUDA version)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --default-timeout=2000 torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --default-timeout=2000 -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application code (excluded: dataset/, models/, __pycache__ via .dockerignore)
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TORCH_HOME=/app/models

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run API
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
