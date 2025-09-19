# Docker Port Conflict Fix Testing Instructions

This document provides comprehensive instructions for testing the Docker port conflict fix implementation locally. The fix implements dynamic port allocation to resolve conflicts when running multiple Docker containers simultaneously.

## Overview

The Docker port conflict fix addresses the issue where multiple containers using the same host port (8888) would cause "port already in use" errors. The solution automatically allocates unique available ports for each container instance.

## Prerequisites

### System Requirements

- Docker installed and running
- Python 3.7+ installed
- `sudo` access for Docker commands (if user not in docker group)

### Required Tools

```bash
# Verify Docker installation
docker --version

# Verify Python installation
python --version

# Install required Python packages
pip install pytest pytest-cov requests

# Verify Docker is running
docker info
```

### Environment Setup

1. **Add user to docker group (optional but recommended)**:

   ```bash
   sudo usermod -aG docker $USER
   newgrp docker  # Apply group membership immediately
   ```

2. **Verify Docker permissions**:

   ```bash
   docker run hello-world
   ```

3. **Clone and navigate to the project**:
   ```bash
   cd /path/to/vits-tts-vietnamese
   ```

## Testing Approach

The testing strategy covers multiple scenarios to ensure the dynamic port allocation works correctly:

1. **Unit testing** - Test port allocation logic
2. **Integration testing** - Test Docker container startup with dynamic ports
3. **Parallel testing** - Test multiple containers simultaneously
4. **Conflict resolution** - Verify no port conflicts occur

## Step-by-Step Testing Instructions

### 1. Build the Docker Image

```bash
# Build the test Docker image
docker build -t vits-tts-vietnamese:test .

# Verify image was created successfully
docker images | grep vits-tts-vietnamese
```

**Expected Result**: Docker image `vits-tts-vietnamese:test` should be built successfully.

### 2. Test Dynamic Port Allocation Logic

```bash
# Run the dynamic port test script
python test_dynamic_ports.py
```

**Expected Result**: The test should pass with output like:

```
Testing dynamic port allocation...
Free ports allocated: 54321, 54322
Starting container on port 54321...
SUCCESS: Health endpoint responded correctly!
Can allocate another free port: 54323

✅ Dynamic port allocation test PASSED!
```

### 3. Run Individual Integration Tests

#### Test API Endpoints

```bash
# Run all integration tests
pytest tests/integration/test_api_endpoints.py -v

# Run specific test function
pytest tests/integration/test_api_endpoints.py::test_health_endpoint -v
```

**Expected Result**: All tests should pass, demonstrating that dynamic ports work correctly for individual test scenarios.

#### Test Model Switching

```bash
pytest tests/integration/test_model_switching.py -v
```

**Expected Result**: Tests should pass, showing that different models can run on different ports without conflicts.

#### Test Error Scenarios

```bash
pytest tests/integration/test_error_scenarios.py -v
```

**Expected Result**: Tests should verify proper error handling with dynamic port allocation.

### 4. Test Parallel Execution

#### Run All Integration Tests in Parallel

```bash
# Run all integration tests with parallel execution
pytest tests/integration -v --tb=short
```

**Expected Result**: All tests should run simultaneously without port conflicts.

#### Manual Parallel Testing

```bash
# Terminal 1: Start first container
docker run -d --name test-container-1 \
  -p $(python -c "import socket; s=socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()"):8888 \
  -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
  -e LOG_LEVEL=DEBUG \
  vits-tts-vietnamese:test

# Terminal 2: Start second container
docker run -d --name test-container-2 \
  -p $(python -c "import socket; s=socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()"):8888 \
  -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
  -e LOG_LEVEL=DEBUG \
  vits-tts-vietnamese:test

# Verify both containers are running on different ports
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Test both containers
curl http://localhost:PORT1/health
curl http://localhost:PORT2/health

# Cleanup
docker stop test-container-1 test-container-2
docker rm test-container-1 test-container-2
```

**Expected Result**: Both containers should run simultaneously on different ports, both responding to health checks.

### 5. Test Custom Port Allocation Script

```bash
# Use the provided integration test script
chmod +x scripts/docker_integration_test.sh
sudo ./scripts/docker_integration_test.sh
```

**Expected Result**: The comprehensive integration test should pass, covering all scenarios including dynamic port allocation.

### 6. Test with Docker Compose (Optional)

```bash
# Test docker-compose configuration
docker-compose up -d

# Test the service
curl http://localhost:8888/health

# Clean up
docker-compose down
```

**Expected Result**: Service should start successfully on port 8888.

## Expected Results and Success Indicators

### Successful Test Outcomes

#### Dynamic Port Allocation

- ✅ Each container gets a unique port
- ✅ No "port already in use" errors
- ✅ Ports are in the valid range (1024-65535)
- ✅ Port allocation is deterministic but unique

#### Container Functionality

- ✅ All containers start successfully
- ✅ Health endpoints return 200 OK
- ✅ TTS endpoints generate valid audio
- ✅ Audio files are accessible via dynamic ports
- ✅ Different models work on different ports

#### Parallel Execution

- ✅ Multiple containers run simultaneously
- ✅ No resource conflicts between containers
- ✅ Each container maintains independent functionality
- ✅ Cleanup works properly after parallel tests

### Log Analysis

During testing, monitor for these success indicators in container logs:

```bash
# Check container logs for successful startup
docker logs CONTAINER_NAME

# Look for these success messages:
# - "TTS service starting on port 8888"
# - "Health check endpoint available"
# - "Model loaded successfully"
# - "Server ready to accept connections"
```

### Error Scenarios to Verify

The fix should handle these scenarios gracefully:

1. **Port exhaustion**: Should handle when many ports are in use
2. **Container failures**: Should clean up properly even if containers fail
3. **Network issues**: Should handle network connectivity problems
4. **Resource limits**: Should work within system resource constraints

## Troubleshooting Tips

### Common Issues and Solutions

#### 1. Docker Permission Issues

**Problem**: `permission denied while trying to connect to the Docker daemon socket`

**Solutions**:

```bash
# Option 1: Use sudo for Docker commands
sudo docker build -t vits-tts-vietnamese:test .

# Option 2: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Option 3: Verify Docker service is running
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. Port Allocation Failures

**Problem**: Port allocation returns the same port multiple times

**Solutions**:

```bash
# Check for port conflicts
netstat -tuln | grep :8888

# Kill processes using port 8888
sudo lsof -ti:8888 | xargs kill -9 || true

# Test port allocation function independently
python -c "
import socket
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        return s.getsockname()[1]

for i in range(5):
    print(f'Port {i}: {get_free_port()}')
"
```

#### 3. Container Startup Failures

**Problem**: Containers fail to start with dynamic ports

**Solutions**:

```bash
# Check Docker daemon logs
sudo journalctl -u docker.service

# Test container with static port first
docker run --rm -p 8888:8888 vits-tts-vietnamese:test

# Verify image integrity
docker run --rm vits-tts-vietnamese:test python -c "import sys; print('Python version:', sys.version)"
```

#### 4. Test Failures

**Problem**: Integration tests fail with port-related errors

**Solutions**:

```bash
# Clean up any existing test containers
docker stop $(docker ps -q --filter "name=vits-tts-test") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=vits-tts-test") 2>/dev/null || true

# Remove test images
docker rmi vits-tts-vietnamese:test 2>/dev/null || true

# Rebuild image
docker build -t vits-tts-vietnamese:test .

# Run tests with verbose output
pytest tests/integration -v --tb=long
```

#### 5. Network Connectivity Issues

**Problem**: Cannot reach container endpoints

**Solutions**:

```bash
# Check if containers are running
docker ps

# Check network settings
docker inspect CONTAINER_ID | grep -A 10 "NetworkSettings"

# Test connectivity to container
docker exec CONTAINER_NAME curl -I http://localhost:8888/health

# Check firewall settings
sudo ufw status
```

### Debug Commands

```bash
# Monitor Docker events in real-time
docker events --filter "event=start" --filter "event=stop"

# Check container resource usage
docker stats

# Inspect container network configuration
docker inspect CONTAINER_NAME | grep -A 20 "NetworkSettings"

# Test port availability
netstat -tuln | grep :PORT_NUMBER

# Check system port usage
ss -tuln | grep LISTEN
```

## Advanced Testing Scenarios

### 1. Stress Testing

```bash
# Test with many concurrent containers
for i in {1..10}; do
  docker run -d --name stress-test-$i \
    -p $(python -c "import socket; s=socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()"):8888 \
    -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
    -e LOG_LEVEL=DEBUG \
    vits-tts-vietnamese:test
done

# Verify all containers are running
docker ps | grep stress-test

# Test each container
for i in {1..10}; do
  PORT=$(docker port stress-test-$i 8888 | cut -d: -f2)
  echo "Testing container $i on port $PORT"
  curl -s http://localhost:$PORT/health | jq .
done

# Cleanup
docker stop stress-test-{1..10}
docker rm stress-test-{1..10}
```

### 2. Port Range Testing

```bash
# Test with specific port ranges
for port in {8000..8100}; do
  if ! netstat -tuln | grep -q ":$port "; then
    echo "Port $port is available"
    docker run --rm --name test-port-$port \
      -p $port:8888 \
      -e TTS_AUDIO_OUTPUT_DIR=/app/audio \
      vits-tts-vietnamese:test &
    sleep 5
    curl -s http://localhost:$port/health && echo "Port $port: SUCCESS" || echo "Port $port: FAILED"
    docker stop test-port-$port 2>/dev/null || true
  fi
done
```

## Cleanup Procedures

### Automated Cleanup

The test suite includes automatic cleanup, but you can manually clean up:

```bash
# Stop and remove test containers
docker stop $(docker ps -q --filter "name=vits-tts-test") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=vits-tts-test") 2>/dev/null || true

# Remove test images
docker rmi vits-tts-vietnamese:test 2>/dev/null || true

# Clean up orphaned containers
docker system prune -f

# Clean up all unused resources
docker system prune -a -f --volumes
```

### Port Cleanup

```bash
# Kill processes using common test ports
for port in 8888 8889 8890 8891 8892; do
  sudo lsof -ti:$port | xargs kill -9 2>/dev/null || true
done
```

## Best Practices

### 1. Regular Testing

- Run the dynamic port tests before each development session
- Include port conflict tests in your CI/CD pipeline
- Test after any changes to Docker configuration

### 2. Monitoring

- Monitor port allocation patterns during development
- Keep track of which ports are commonly used
- Document any unusual port allocation behavior

### 3. Documentation

- Update this document when testing procedures change
- Document any new test scenarios or edge cases
- Share testing results with the development team

### 4. Environment Consistency

- Test in environments similar to production
- Consider different operating systems and Docker versions
- Test both with and without Docker group membership

## Related Files

### Implementation Files

- [`tests/integration/conftest.py`](tests/integration/conftest.py) - Dynamic port allocation implementation
- [`test_dynamic_ports.py`](test_dynamic_ports.py) - Standalone port testing script
- [`scripts/docker_integration_test.sh`](scripts/docker_integration_test.sh) - Comprehensive integration test

### Configuration Files

- [`Dockerfile`](Dockerfile) - Container build configuration
- [`docker-compose.yml`](docker-compose.yml) - Development environment setup
- [`.github/workflows/docker-test.yml`](.github/workflows/docker-test.yml) - CI/CD pipeline configuration

### Documentation

- [`docs/DOCKER_TESTING_REPORT.md`](docs/DOCKER_TESTING_REPORT.md) - Previous testing results
- [`tests/integration/README.md`](tests/integration/README.md) - Integration test overview

## Conclusion

The Docker port conflict fix implementation provides a robust solution for dynamic port allocation. By following these testing instructions, you can verify that the fix works correctly in your local environment and ensure reliable operation in production scenarios.

**Key Success Factors**:

- ✅ Dynamic port allocation works correctly
- ✅ No port conflicts during parallel execution
- ✅ All container functionality preserved
- ✅ Proper cleanup and resource management
- ✅ Comprehensive error handling

Regular testing of this implementation will help maintain system reliability and prevent future port-related issues.
