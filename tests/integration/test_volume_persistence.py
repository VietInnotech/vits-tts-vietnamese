"""Integration tests for volume persistence in Docker containers."""

import os
import socket
import tempfile
import shutil
import requests
import pytest
import subprocess
import time
from typing import Generator, Dict, Any


def get_free_port() -> int:
    """Get a free port number by binding to port 0 and returning the assigned port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope="function")
def temp_audio_dir() -> Generator[str, None, None]:
    """Create a temporary directory for audio output."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after tests
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def docker_container_with_volume(docker_image: str, temp_audio_dir: str) -> Generator[Dict[str, Any], None, None]:
    """Run a Docker container with volume mount for testing."""
    container_name = "vits-tts-test-container-volume"
    port = get_free_port()
    
    try:
        # Run the container with volume mount
        process = subprocess.Popen([
            "docker", "run", "--name", container_name,
            "-p", f"{port}:8888",
            "-v", f"{temp_audio_dir}:/app/audio",
            "-e", "TTS_AUDIO_OUTPUT_DIR=/app/audio",
            "-e", "LOG_LEVEL=DEBUG",
            docker_image
        ])
        
        # Wait for the container to start
        time.sleep(10)
        
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "-f", f"name={container_name}"],
            capture_output=True,
            text=True
        )
        
        if container_name not in result.stdout:
            # Container failed to start, get logs
            logs_result = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True
            )
            pytest.fail(f"Container failed to start. Logs: {logs_result.stdout}\n{logs_result.stderr}")
        
        # Wait for the service to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                if i == max_retries - 1:
                    pytest.fail("Service did not become ready in time")
                time.sleep(2)
        
        yield {
            "name": container_name,
            "host": "localhost",
            "port": port,
            "audio_dir": temp_audio_dir
        }
        
    except Exception as e:
        pytest.fail(f"Failed to start container: {str(e)}")
    finally:
        # Stop and remove the container
        try:
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True
            )
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True
            )
        except (subprocess.CalledProcessError, Exception):
            pass  # Ignore cleanup errors


def test_audio_file_persistence(docker_container_with_volume: Dict[str, Any]) -> None:
    """Test that generated audio files persist in the mounted volume."""
    # Generate an audio file
    url = f"http://{docker_container_with_volume['host']}:{docker_container_with_volume['port']}/tts"
    params = {
        "text": "Kiểm tra tính bền vững của tệp âm thanh",
        "speed": "normal"
    }
    
    response = requests.get(url, params=params)
    assert response.status_code == 200
    data = response.json()
    
    # Check that the audio file exists in the volume
    audio_filename = data["audio_url"].split("/")[-1]
    audio_file_path = os.path.join(docker_container_with_volume["audio_dir"], audio_filename)
    
    assert os.path.exists(audio_file_path), f"Audio file {audio_filename} not found in volume"
    assert os.path.getsize(audio_file_path) > 0, f"Audio file {audio_filename} is empty"
    
    # Verify it's a valid WAV file
    with open(audio_file_path, "rb") as f:
        file_content = f.read()
        assert file_content.startswith(b"RIFF"), "Audio file is not a valid WAV file"


def test_audio_file_accessibility(docker_container_with_volume: Dict[str, Any]) -> None:
    """Test that audio files in the volume are accessible via the API."""
    # Generate an audio file
    tts_url = f"http://{docker_container_with_volume['host']}:{docker_container_with_volume['port']}/tts"
    params = {
        "text": "Kiểm tra khả năng truy cập tệp âm thanh",
        "speed": "normal"
    }
    
    tts_response = requests.get(tts_url, params=params)
    assert tts_response.status_code == 200
    tts_data = tts_response.json()
    
    # Check that the audio file exists in the volume
    audio_filename = tts_data["audio_url"].split("/")[-1]
    audio_file_path = os.path.join(docker_container_with_volume["audio_dir"], audio_filename)
    
    assert os.path.exists(audio_file_path), f"Audio file {audio_filename} not found in volume"
    
    # Now try to access the audio file via the API
    audio_url = f"http://{docker_container_with_volume['host']}:{docker_container_with_volume['port']}{tts_data['audio_url']}"
    audio_response = requests.get(audio_url)
    
    assert audio_response.status_code == 200
    assert audio_response.headers.get("content-type") == "audio/wav"
    assert len(audio_response.content) > 0


def test_multiple_audio_files_persistence(docker_container_with_volume: Dict[str, Any]) -> None:
    """Test that multiple audio files are persisted correctly."""
    texts = [
        "Tệp âm thanh đầu tiên",
        "Tệp âm thanh thứ hai",
        "Tệp âm thanh thứ ba"
    ]
    
    generated_files = []
    
    # Generate multiple audio files
    for text in texts:
        url = f"http://{docker_container_with_volume['host']}:{docker_container_with_volume['port']}/tts"
        params = {
            "text": text,
            "speed": "normal"
        }
        
        response = requests.get(url, params=params)
        assert response.status_code == 200
        data = response.json()
        
        audio_filename = data["audio_url"].split("/")[-1]
        generated_files.append(audio_filename)
    
    # Check that all files exist in the volume
    for filename in generated_files:
        audio_file_path = os.path.join(docker_container_with_volume["audio_dir"], filename)
        assert os.path.exists(audio_file_path), f"Audio file {filename} not found in volume"
        assert os.path.getsize(audio_file_path) > 0, f"Audio file {filename} is empty"


def test_volume_permissions(docker_container_with_volume: Dict[str, Any]) -> None:
    """Test that the volume has correct permissions for file operations."""
    # Generate an audio file
    url = f"http://{docker_container_with_volume['host']}:{docker_container_with_volume['port']}/tts"
    params = {
        "text": "Kiểm tra quyền truy cập volume",
        "speed": "normal"
    }
    
    response = requests.get(url, params=params)
    assert response.status_code == 200
    
    # Check that we can read from the volume
    files = os.listdir(docker_container_with_volume["audio_dir"])
    assert len(files) > 0, "No files found in volume directory"
    
    # Check that files are readable
    for filename in files:
        file_path = os.path.join(docker_container_with_volume["audio_dir"], filename)
        assert os.access(file_path, os.R_OK), f"File {filename} is not readable"