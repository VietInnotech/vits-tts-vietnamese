#!/bin/bash
# Test script to reproduce the Docker TTS issue

echo "Building Docker image..."
docker build -t vits-tts-test:latest .

echo "Running Docker container with volume mount..."
mkdir -p test_audio_output

# Run container with volume mount
docker run -d --name vits-tts-test-container \
  -p 8888:8888 \
  -v "$(pwd)/test_audio_output:/app/audio" \
  -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
  -e LOG_LEVEL=DEBUG \
  vits-tts-test:latest

echo "Waiting for container to start..."
sleep 15

echo "Checking container status..."
docker ps -f name=vits-tts-test-container

echo "Testing health endpoint..."
curl -f http://localhost:8888/health || echo "Health check failed"

echo "Testing TTS endpoint..."
curl -f "http://localhost:8888/tts?text=Hello%20World&speed=normal" || echo "TTS endpoint failed"

echo "Getting container logs..."
docker logs vits-tts-test-container

echo "Checking audio directory permissions..."
docker exec vits-tts-test-container ls -la /app/audio
docker exec vits-tts-test-container whoami
docker exec vits-tts-test-container ls -la /app/

echo "Cleaning up..."
docker stop vits-tts-test-container
docker rm vits-tts-test-container
rm -rf test_audio_output

echo "Test completed."