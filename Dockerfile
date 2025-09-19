# Use Python <3.13 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p audio logs models

# Copy models - bundle both default models in the image
COPY models/infore/ models/infore/
COPY models/v2/ models/v2/

# Copy configuration files
COPY configs/ configs/

# Copy source code
COPY src/ src/
COPY start.sh ./

# Make start script executable
RUN chmod +x start.sh

# Expose the port the app runs on
EXPOSE 8888

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Environment variables for configuration
# These can be overridden at runtime to customize the service
# TTS_MODEL_PATH - Path to the ONNX model file
# TTS_CONFIG_PATH - Path to the model config JSON
# TTS_AUDIO_OUTPUT_DIR - Directory for audio output
# TTS_CACHE_SIZE - Cache size for TTS responses
# TTS_DEFAULT_SPEED - Default speech speed
# TTS_NOISE_SCALE - Noise scale parameter
# TTS_NOISE_W - Noise W parameter
# SERVER_PORT - Server port
# LOG_LEVEL - Logging level

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# Run the application
CMD ["./start.sh"]