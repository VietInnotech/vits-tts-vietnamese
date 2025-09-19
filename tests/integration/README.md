# Integration Tests for VITS-TTS Vietnamese Docker Container

This directory contains integration tests that verify the functionality of the VITS-TTS Vietnamese service when running in a Docker container.

## Test Structure

- `conftest.py` - Pytest configuration and Docker fixtures
- `test_api_endpoints.py` - Tests for API endpoints
- `test_model_switching.py` - Tests for model switching functionality
- `test_volume_persistence.py` - Tests for volume persistence
- `test_error_scenarios.py` - Tests for error scenarios and edge cases

## Prerequisites

- Docker installed and running
- Python 3.7+
- Required Python packages (see `requirements.txt`)

## Running the Tests

### Run All Integration Tests

```bash
pytest tests/integration -v
```

### Run Specific Test File

```bash
pytest tests/integration/test_api_endpoints.py -v
```

### Run Tests with Coverage

```bash
coverage run -m pytest tests/integration
coverage report
coverage html
```

## Test Organization

### API Endpoints Tests

These tests verify that all API endpoints work correctly:

- Health check endpoint (`/health`)
- TTS generation endpoint (`/tts`)
- TTS streaming endpoint (`/tts/stream`)
- Documentation endpoint (`/docs`)
- Root redirect endpoint (`/`)

### Model Switching Tests

These tests verify that different models can be used by setting environment variables:

- Default model (V2)
- InfoRE model
- V2 model (explicit)
- Model consistency checks

### Volume Persistence Tests

These tests verify that data persists correctly when using Docker volumes:

- Audio file persistence
- Audio file accessibility
- Multiple audio files persistence
- Volume permissions
- Volume isolation

### Error Scenarios Tests

These tests verify that the service handles error conditions gracefully:

- Invalid endpoints
- Missing parameters
- Invalid parameters
- Long text inputs
- Special characters and Unicode
- Concurrent requests
- Different HTTP methods
- Large payload handling

## Docker Fixtures

The tests use the following Docker fixtures defined in `conftest.py`:

- `docker_image` - Builds the Docker image for testing
- `docker_container` - Runs a container with default settings
- `docker_container_infore_model` - Runs a container with InfoRE model
- `docker_container_v2_model` - Runs a container with V2 model
- `docker_container_with_volume` - Runs a container with volume mount

## Environment Variables

The tests use the following environment variables for configuration:

- `TTS_MODEL_PATH` - Path to the ONNX model file
- `TTS_CONFIG_PATH` - Path to the model config JSON
- `TTS_AUDIO_OUTPUT_DIR` - Directory for audio output
- `LOG_LEVEL` - Logging level

## Dynamic Port Allocation

The integration tests now use dynamic port allocation to prevent conflicts during parallel test execution. This feature automatically finds available ports for each test container.

### How It Works

The [`get_free_port()`](tests/integration/conftest.py) function in [`conftest.py`](tests/integration/conftest.py) automatically detects available TCP ports and assigns them to test containers:

```python
def get_free_port():
    """Get a free port on the host system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port
```

### Benefits

- ✅ **No Port Conflicts**: Each test gets a unique port, eliminating "port already in use" errors
- ✅ **Parallel Testing**: Multiple tests can run simultaneously without interference
- ✅ **Dynamic Assignment**: Ports are assigned at runtime, ensuring availability
- ✅ **Proper Cleanup**: Resources are automatically cleaned up after each test

### Implementation Details

- All Docker fixtures in [`conftest.py`](tests/integration/conftest.py) use dynamic ports
- Each test container gets its own unique port allocation
- The system automatically handles port binding and cleanup
- No manual port management required for developers

## Cleanup

The tests automatically clean up Docker containers and images after running. The dynamic port allocation system ensures that containers are properly cleaned up even if tests fail:

```bash
# All test containers are automatically cleaned up after each test
# No manual port-specific cleanup needed

# If you need to manually clean up any remaining containers:
docker stop $(docker ps -q --filter "name=vits-tts-test")
docker rm $(docker ps -aq --filter "name=vits-tts-test")
```

**Key Features:**

- Automatic container cleanup after each test
- Dynamic port allocation prevents resource conflicts
- Proper resource management even on test failures
- No manual port management required
