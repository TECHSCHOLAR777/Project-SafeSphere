FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

# System deps for media/ML/Audio and OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        libsndfile1 \
        libsm6 \
        libxrender1 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy a cleaned requirements file provided for container builds
COPY requirements_hf.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy the Heatmap app
COPY . /app

EXPOSE ${PORT}

# Small startup wrapper ensures PORT is respected
CMD ["/bin/sh", "/app/Heatmap/start.sh"]
