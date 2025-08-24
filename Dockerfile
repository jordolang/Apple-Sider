# Apple Sider - Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    exiftool \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clone and setup CLI-Music-Downloader
RUN git clone https://github.com/yourusername/CLI-Music-Downloader.git /app/cli-music-downloader \
    && cd /app/cli-music-downloader \
    && pip install -r requirements.txt \
    && chmod +x bin/download_music \
    && mkdir -p /app/downloads /app/config

# Copy application code
COPY app/ /app/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV CLI_MUSIC_DOWNLOADER_PATH=/app/cli-music-downloader/bin/download_music
ENV DOWNLOAD_PATH=/app/downloads
ENV CONFIG_PATH=/app/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

# Start the application
CMD ["python", "app.py"]
