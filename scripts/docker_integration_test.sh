#!/bin/bash
# Docker Integration Test Script for VITS-TTS Vietnamese

set -euo pipefail

echo "=== VITS-TTS Vietnamese Docker Integration Tests ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

# Function to report test results
report_test() {
    local test_name="$1"
    local result="$2"
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $test_name"
        ((FAILED++))
    fi
}

# Function to make HTTP requests
make_request() {
    local url="$1"
    local expected_status="${2:-200}"
    local method="${3:-GET}"
    
    if response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" 2>/dev/null); then
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" = "$expected_status" ]; then
            echo "$body"
            return 0
        else
            echo "Expected $expected_status, got $http_code" >&2
            return 1
        fi
    else
        echo "Request failed" >&2
        return 1
    fi
}

# Function to URL encode text
urlencode() {
    python3 -c "import urllib.parse; print(urllib.parse.quote('''$1'''))"
}

echo "1. Testing Docker image availability..."
if sudo docker images | grep -q "vits-tts-vietnamese.*test"; then
    report_test "Docker image exists" "PASS"
else
    report_test "Docker image exists" "FAIL"
    echo "Docker image 'vits-tts-vietnamese:test' not found. Please build it first."
    exit 1
fi

echo
echo "2. Testing container startup and health check..."

# Start container
echo "Starting container..."
CONTAINER_ID=$(sudo docker run -d --name vits-integration-test \
    -p 8888:8888 \
    -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
    -e LOG_LEVEL=DEBUG \
    vits-tts-vietnamese:test)

# Wait for container to be ready
echo "Waiting for container to be ready..."
for i in {1..30}; do
    if sudo docker exec "$CONTAINER_ID" curl -s -f http://localhost:8888/health >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Test health endpoint
echo "Testing health endpoint..."
if response=$(make_request "http://localhost:8888/health"); then
    if echo "$response" | grep -q '"status":"healthy"'; then
        report_test "Health endpoint returns healthy status" "PASS"
    else
        report_test "Health endpoint returns healthy status" "FAIL"
        echo "Response: $response"
    fi
else
    report_test "Health endpoint accessible" "FAIL"
fi

echo
echo "3. Testing TTS functionality..."

# Test TTS endpoint with Vietnamese text
VIETNAMESE_TEXT="Xin chào Việt Nam!"
ENCODED_TEXT=$(urlencode "$VIETNAMESE_TEXT")

echo "Testing TTS endpoint..."
if response=$(make_request "http://localhost:8888/tts?text=$ENCODED_TEXT&speed=normal"); then
    if echo "$response" | grep -q '"text":"'"$VIETNAMESE_TEXT"'"'; then
        report_test "TTS endpoint processes Vietnamese text" "PASS"
        
        # Extract audio URL
        AUDIO_URL=$(echo "$response" | grep -o '"audio_url":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$AUDIO_URL" ]; then
            report_test "TTS endpoint returns audio URL" "PASS"
            
            # Test audio file access
            echo "Testing audio file access..."
            if make_request "http://localhost:8888$AUDIO_URL" >/dev/null; then
                report_test "Audio file is accessible" "PASS"
            else
                report_test "Audio file is accessible" "FAIL"
            fi
        else
            report_test "TTS endpoint returns audio URL" "FAIL"
        fi
    else
        report_test "TTS endpoint processes Vietnamese text" "FAIL"
        echo "Response: $response"
    fi
else
    report_test "TTS endpoint accessible" "FAIL"
fi

echo
echo "4. Testing TTS streaming endpoint..."

if audio_data=$(make_request "http://localhost:8888/tts/stream?text=$ENCODED_TEXT&speed=normal"); then
    # Check if it's valid WAV data
    if echo "$audio_data" | file - | grep -q "WAVE audio"; then
        report_test "TTS streaming returns valid WAV audio" "PASS"
    else
        report_test "TTS streaming returns valid WAV audio" "FAIL"
    fi
else
    report_test "TTS streaming endpoint accessible" "FAIL"
fi

echo
echo "5. Testing different speeds..."

for speed in slow normal fast; do
    echo "Testing speed: $speed"
    if response=$(make_request "http://localhost:8888/tts?text=$ENCODED_TEXT&speed=$speed"); then
        if echo "$response" | grep -q "\"speed\":\"$speed\""; then
            report_test "Speed parameter '$speed' works" "PASS"
        else
            report_test "Speed parameter '$speed' works" "FAIL"
        fi
    else
        report_test "Speed parameter '$speed' endpoint" "FAIL"
    fi
done

echo
echo "6. Testing error handling..."

# Test empty text
if response=$(make_request "http://localhost:8888/tts?text=&speed=normal" "200"); then
    report_test "Empty text handling" "PASS"
else
    report_test "Empty text handling" "FAIL"
fi

# Test invalid endpoint
if response=$(make_request "http://localhost:8888/invalid-endpoint" "404"); then
    report_test "Invalid endpoint returns 404" "PASS"
else
    report_test "Invalid endpoint returns 404" "FAIL"
fi

echo
echo "7. Testing volume persistence..."

# Create test directories
mkdir -p /tmp/test_audio
mkdir -p /tmp/test_logs

# Start container with volume mounts
sudo docker stop vits-integration-test >/dev/null 2>&1 || true
sudo docker rm vits-integration-test >/dev/null 2>&1 || true

CONTAINER_ID=$(sudo docker run -d --name vits-volume-test \
    -p 8889:8888 \
    -v /tmp/test_audio:/app/audio \
    -v /tmp/test_logs:/app/data/logs \
    -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
    -e LOG_LEVEL=DEBUG \
    vits-tts-vietnamese:test)

# Wait for container to be ready
for i in {1..30}; do
    if sudo docker exec "$CONTAINER_ID" curl -s -f http://localhost:8888/health >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Generate audio file
ENCODED_TEXT2=$(urlencode "Testing volume persistence")
if response=$(make_request "http://localhost:8889/tts?text=$ENCODED_TEXT2&speed=normal"); then
    AUDIO_URL=$(echo "$response" | grep -o '"audio_url":"[^"]*"' | cut -d'"' -f4)
    FILENAME=$(basename "$AUDIO_URL")
    
    # Check if file exists in host volume
    if [ -f "/tmp/test_audio/$FILENAME" ]; then
        report_test "Audio file persists in host volume" "PASS"
    else
        report_test "Audio file persists in host volume" "FAIL"
    fi
else
    report_test "Volume persistence test" "FAIL"
fi

echo
echo "8. Testing model switching..."

# Test with InfoRE model
sudo docker stop vits-volume-test >/dev/null 2>&1 || true
sudo docker rm vits-volume-test >/dev/null 2>&1 || true

CONTAINER_ID=$(sudo docker run -d --name vits-infore-test \
    -p 8890:8888 \
    -e TTS_MODEL_PATH=models/infore/vi_VN-vais1000-medium.onnx \
    -e TTS_CONFIG_PATH=models/infore/vi_VN-vais1000-medium.onnx.json \
    -e LOG_LEVEL=DEBUG \
    vits-tts-vietnamese:test)

# Wait for container to be ready
for i in {1..30}; do
    if sudo docker exec "$CONTAINER_ID" curl -s -f http://localhost:8888/health >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

if response=$(make_request "http://localhost:8890/tts?text=$ENCODED_TEXT&speed=normal"); then
    if echo "$response" | grep -q '"text":"'"$VIETNAMESE_TEXT"'"'; then
        report_test "InfoRE model switching works" "PASS"
    else
        report_test "InfoRE model switching works" "FAIL"
        echo "Response: $response"
    fi
else
    report_test "InfoRE model switching endpoint" "FAIL"
fi

echo
echo "9. Cleanup..."

# Stop and remove containers
sudo docker stop vits-infore-test >/dev/null 2>&1 || true
sudo docker rm vits-infore-test >/dev/null 2>&1 || true

# Clean up test directories
rm -rf /tmp/test_audio /tmp/test_logs

report_test "Cleanup completed" "PASS"

echo
echo "=== Test Summary ==="
echo -e "Tests passed: ${GREEN}$PASSED${NC}"
echo -e "Tests failed: ${RED}$FAILED${NC}"
echo -e "Total tests: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi