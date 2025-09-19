# Docker Configuration Guide

This document provides comprehensive instructions for configuring and running the VITS-TTS Vietnamese service using Docker, including support for bundled models and environment variable customization.

## Overview

The Docker container provides a portable, production-ready deployment of the Vietnamese TTS service with the following key features:

- **Bundled Models**: Both Vietnamese TTS models are included in the image
- **Environment Variables**: Flexible configuration at runtime
- **Volume Mounts**: Persistent storage for audio output and logs
- **Health Checks**: Built-in health monitoring endpoint
- **Security**: Non-root user execution

## Bundled Models

The Docker image includes both Vietnamese TTS models, making it completely self-contained:

### 1. InfoRE Model

- **Path**: `models/infore/vi_VN-vais1000-medium.onnx`
- **Config**: `models/infore/vi_VN-vais1000-medium.onnx.json`
- **Size**: ~63.2 MB
- **Characteristics**: General Vietnamese TTS model with good quality

### 2. Fine-tuned V2 Model (Default)

- **Path**: `models/v2/finetuning_pretrained_vi.onnx`
- **Config**: `models/v2/finetuning_pretrained_vi.onnx.json`
- **Size**: ~63.1 MB
- **Characteristics**: Fine-tuned model optimized for better Vietnamese pronunciation

### Model Selection Logic

The service automatically uses the V2 model by default. To switch between models, use the `TTS_MODEL_PATH` and `TTS_CONFIG_PATH` environment variables.

## Available Environment Variables

| Variable               | Description                   | Default Value                                  | Example                                         |
| ---------------------- | ----------------------------- | ---------------------------------------------- | ----------------------------------------------- |
| `TTS_MODEL_PATH`       | Path to the ONNX model file   | `models/v2/finetuning_pretrained_vi.onnx`      | `models/infore/vi_VN-vais1000-medium.onnx`      |
| `TTS_CONFIG_PATH`      | Path to the model config JSON | `models/v2/finetuning_pretrained_vi.onnx.json` | `models/infore/vi_VN-vais1000-medium.onnx.json` |
| `TTS_AUDIO_OUTPUT_DIR` | Directory for audio output    | `audio/`                                       | `output/`                                       |
| `TTS_CACHE_SIZE`       | Cache size for TTS responses  | `100`                                          | `200`                                           |
| `TTS_DEFAULT_SPEED`    | Default speech speed          | `normal`                                       | `fast`                                          |
| `TTS_NOISE_SCALE`      | Noise scale parameter         | `0.4`                                          | `0.5`                                           |
| `TTS_NOISE_W`          | Noise W parameter             | `0.5`                                          | `0.6`                                           |
| `SERVER_PORT`          | Server port                   | `8888`                                         | `9000`                                          |
| `LOG_LEVEL`            | Logging level                 | `INFO`                                         | `DEBUG`                                         |

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

This command:

- Builds the Docker image with bundled models
- Starts the service on port 8888
- Mounts source code, configs, audio, and logs for development
- Provides live code reloading during development

### Option 2: Using Docker Directly

```bash
# Build the image
docker build -t vits-tts-vietnamese .

# Run with default settings
docker run -d -p 8888:8888 vits-tts-vietnamese

# Run with custom settings
docker run -d \
  -e TTS_MODEL_PATH=models/infore/vi_VN-vais1000-medium.onnx \
  -e TTS_CONFIG_PATH=models/infore/vi_VN-vais1000-medium.onnx.json \
  -e SERVER_PORT=8888 \
  -p 8888:8888 \
  vits-tts-vietnamese
```

## Detailed Configuration

### Docker Compose Configuration

The [`docker-compose.yml`](docker-compose.yml:1) file provides a development-friendly setup:

```yaml
services:
  vits-tts:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8888:8888"
    volumes:
      - ./src:/app/src # Live code reloading
      - ./configs:/app/configs # Configuration files
      - ./audio:/app/audio # Persistent audio output
      - ./logs:/app/logs # Application logs
    environment:
      - PYTHONPATH=/app/src
      # Uncomment to override default model:
      # - TTS_MODEL_PATH=models/infore/vi_VN-vais1000-medium.onnx
      # - TTS_CONFIG_PATH=models/infore/vi_VN-vais1000-medium.onnx.json
    command: ["./start.sh"]
```

### Volume Mounts

The following directories are mounted for persistence and development:

| Mount Point    | Host Directory | Description                  |
| -------------- | -------------- | ---------------------------- |
| `/app/src`     | `./src`        | Source code (live reloading) |
| `/app/configs` | `./configs`    | Configuration files          |
| `/app/audio`   | `./audio`      | Generated audio files        |
| `/app/logs`    | `./logs`       | Application logs             |

**Note**: Models are bundled in the image, so no model volume mount is required.

## Model Switching

### Switch to InfoRE Model

```bash
# With Docker Compose
docker-compose up --build -e TTS_MODEL_PATH=models/infore/vi_VN-vais1000-medium.onnx \
  -e TTS_CONFIG_PATH=models/infore/vi_VN-vais1000-medium.onnx.json

# With Docker CLI
docker run -d \
  -e TTS_MODEL_PATH=models/infore/vi_VN-vais1000-medium.onnx \
  -e TTS_CONFIG_PATH=models/infore/vi_VN-vais1000-medium.onnx.json \
  -p 8888:8888 \
  vits-tts-vietnamese
```

### Use Fine-tuned V2 Model (Default)

No environment variables needed - this model is used by default:

```bash
docker run -d -p 8888:8888 vits-tts-vietnamese
```

### Using Custom Models

To use your own model files:

```bash
# Mount custom model directory
docker run -d \
  -v /path/to/your/models:/app/custom_models \
  -e TTS_MODEL_PATH=custom_models/your_model.onnx \
  -e TTS_CONFIG_PATH=custom_models/your_model.json \
  -p 8888:8888 \
  vits-tts-vietnamese
```

## Advanced Configuration

### Production Deployment

For production, consider these optimizations:

```yaml
# docker-compose.prod.yml
services:
  vits-tts:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "80:8888" # Use port 80
    volumes:
      - ./audio:/app/audio # Only mount persistent data
      - ./logs:/app/logs
    environment:
      - PYTHONPATH=/app/src
      - TTS_AUDIO_OUTPUT_DIR=/app/audio
      - TTS_CACHE_SIZE=50 # Reduce cache size
      - LOG_LEVEL=WARNING # Reduce log verbosity
    restart: unless-stopped # Auto-restart on failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Environment Variable Examples

#### High Performance Configuration

```bash
docker run -d \
  -e TTS_CACHE_SIZE=200 \
  -e TTS_NOISE_SCALE=0.3 \
  -e TTS_NOISE_W=0.4 \
  -e LOG_LEVEL=WARNING \
  -p 8888:8888 \
  vits-tts-vietnamese
```

#### Development Configuration

```bash
docker run -d \
  -e TTS_CACHE_SIZE=50 \
  -e TTS_NOISE_SCALE=0.6 \
  -e TTS_NOISE_W=0.7 \
  -e LOG_LEVEL=DEBUG \
  -p 8888:8888 \
  vits-tts-vietnamese
```

## Testing and Verification

### Health Check

Verify the service is running properly:

```bash
curl http://localhost:8888/health
```

Expected response:

```json
{
  "status": "healthy",
  "message": "TTS service is running"
}
```

### TTS Functionality Test

Test the text-to-speech functionality:

```bash
curl -X POST http://localhost:8888/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Xin chào Việt Nam!", "speed": "normal"}'
```

### Model Verification

Check if bundled models are accessible:

```bash
# List available models in container
docker exec <container_name> ls -la /app/models/

# Check specific model files
docker exec <container_name> ls -la /app/models/v2/
docker exec <container_name> ls -la /app/models/infore/
```

## Docker Best Practices

### 1. Image Optimization

- **Multi-stage builds**: Not used for simplicity and to keep models accessible
- **Layer caching**: Dockerfile optimized by copying requirements first
- **Slim base image**: Using Python 3.11-slim for reduced image size
- **Non-root user**: Enhanced security with dedicated application user

### 2. Security Considerations

- **Non-root execution**: Container runs as `appuser` (UID 1000)
- **Environment variables**: Sensitive data management
- **Health checks**: Built-in monitoring for reliability

### 3. Performance Optimization

- **Volume caching**: Efficient volume mount handling
- **Memory usage**: Models loaded into memory for fast inference
- **Caching**: Response caching for repeated requests

### 4. Monitoring and Logging

- **Structured logs**: Consistent log format for easier parsing
- **Health endpoints**: `/health` for monitoring
- **Log levels**: Configurable verbosity for different environments

## Troubleshooting

### Common Issues

#### "Model not found" errors

**Solution**: Verify model paths are correct:

```bash
# Check bundled models
docker exec <container_name> find /app/models -name "*.onnx"

# Verify model file permissions
docker exec <container_name> ls -la /app/models/v2/finetuning_pretrained_vi.onnx
```

#### Container startup failures

**Solution**: Check container logs:

```bash
docker logs <container_name>
docker logs <container_name> --tail 50  # Show last 50 lines
```

#### Port conflicts

**Solution**: Use different port mapping:

```bash
docker run -d -p 8080:8888 vits-tts-vietnamese
```

#### Performance issues

**Solution**: Adjust cache size and logging:

```bash
docker run -d \
  -e TTS_CACHE_SIZE=50 \
  -e LOG_LEVEL=WARNING \
  -p 8888:8888 \
  vits-tts-vietnamese
```

### Debug Mode

For detailed debugging:

```bash
# Run in interactive mode
docker run -it --rm \
  -e LOG_LEVEL=DEBUG \
  -p 8888:8888 \
  vits-tts-vietnamese

# Or attach to running container
docker attach <container_name>
```

### Resource Usage Monitoring

Monitor container resources:

```bash
# Check resource usage
docker stats <container_name>

# Check disk usage
docker exec <container_name> df -h

# Check memory usage
docker exec <container_name> free -h
```

## API Documentation

Once running, access the interactive API documentation at:

```
http://localhost:8888/docs
```

This provides:

- Interactive API testing
- Detailed endpoint documentation
- Request/response examples
- Schema definitions

## Support

For additional support:

- Check the [main README](README.md) for general information
- Review [project documentation](../docs/)
- File issues in the project repository
- Contact the development team
