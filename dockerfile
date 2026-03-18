# -------------------------------
# Stage 1: Base image
# -------------------------------
FROM python:3.11-slim

    # Set working directory
WORKDIR /app
    
    # Install system dependencies (for Gmail, LLM, OpenCV for OCR, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
    
    # -------------------------------
    # Stage 2: Install Python deps
    # -------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
    
    # -------------------------------
    # Stage 3: Copy project files
    # -------------------------------
COPY . .
    
    # -------------------------------
    # Stage 4: Runtime command
    # -------------------------------
CMD ["python", "main.py"]
    