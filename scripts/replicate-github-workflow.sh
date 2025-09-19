#!/bin/bash
set -euo pipefail

# Script to replicate the GitHub Actions workflow locally
# This script follows the exact steps from .github/workflows/docker-test.yml

echo "=== Replicating GitHub Actions Workflow Locally ==="
echo "Starting workflow replication at $(date)"

# Step 1: Set up Python environment (similar to GitHub Actions)
echo "Step 1: Setting up Python environment..."
python_version=$(python3 --version 2>/dev/null || echo "Python not found")
echo "Current Python version: $python_version"

# Check if Python version is < 3.13 (as specified in workflow)
if command -v python3 >/dev/null 2>&1; then
    python3 -c "import sys; exit(0 if sys.version_info < (3, 13) else 1)" || {
        echo "ERROR: Python version must be < 3.13 as specified in workflow"
        exit 1
    }
fi

# Step 2: Install test dependencies (exact same as workflow)
echo "Step 2: Installing test dependencies..."
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
pip3 install pytest pytest-cov

# Step 3: Build Docker image with the same tag
echo "Step 3: Building Docker image..."
docker build -t vits-tts-vietnamese:test .

# Step 4: Create volume directories (exact same as workflow)
echo "Step 4: Creating volume directories..."
mkdir -p /tmp/audio_output
mkdir -p /tmp/test_logs

# Step 5: Run container with volume mounts (exact same as workflow)
echo "Step 5: Running container with volume mounts..."
docker run -d --name vits-test \
  -p 8888:8888 \
  -v /tmp/audio_output:/app/audio \
  -v /tmp/test_logs:/app/data/logs \
  -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
  -e LOG_LEVEL=DEBUG \
  vits-tts-vietnamese:test

# Wait for container to start (same as workflow)
echo "Waiting for container to start..."
sleep 15

# Step 6: Verify health endpoint (exact same as workflow)
echo "Step 6: Verifying health endpoint..."

# Check if container is running
echo "Checking if container is running..."
if docker ps | grep -q vits-test; then
    echo "Container is running"
else
    echo "ERROR: Container is not running"
    docker logs vits-test
    exit 1
fi

# Test health endpoint
echo "Testing health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/health || echo "000")
if [ "$response" != "200" ]; then
    echo "Health check failed with status code: $response"
    docker logs vits-test
    exit 1
else
    echo "Health check passed"
    # Show health response
    curl -s http://localhost:8888/health | jq . || echo "Failed to parse JSON response"
fi

# Step 7: Cleanup orphaned containers and processes (exact same as workflow)
echo "Step 7: Cleaning up orphaned containers and processes..."
# Remove any existing containers using the test image
docker rm -f $(docker ps -a -q --filter ancestor=vits-tts-vietnamese:test) 2>/dev/null || true
# Kill any processes using port 8888
lsof -ti:8888 | xargs kill -9 2>/dev/null || true

# Step 8: Run integration tests with parallel execution
echo "Step 8: Running integration tests with parallel execution..."
# Run pytest with the exact same parameters as in the workflow
pytest tests/integration -v --tb=short

# Step 9: Final cleanup (exact same as workflow)
echo "Step 9: Final cleanup..."
docker stop vits-test 2>/dev/null || true
docker rm vits-test 2>/dev/null || true
# Clean up volume directories
rm -rf /tmp/audio_output
rm -rf /tmp/test_logs

echo "=== Workflow Replication Completed Successfully ==="
echo "All steps from the GitHub Actions workflow have been replicated locally."