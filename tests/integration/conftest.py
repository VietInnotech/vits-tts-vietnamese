"""Pytest configuration and fixtures for integration tests against Docker containers."""

import os
import subprocess
import time
import requests
import pytest
from typing import Generator, Dict, Any


@pytest.fixture(scope="session")
def docker_image() -> Generator[str, None, None]:
    """Build the Docker image for testing."""
    image_name = "vits-tts-vietnamese:test"
    try:
        # Build the Docker image
        subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            check=True,
            capture_output=True,
            cwd=os.getcwd()
        )
        yield image_name
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to build Docker image: {e.stderr.decode()}")
    except Exception as e:
        pytest.fail(f"Failed to build Docker image: {str(e)}")
    finally:
        # Clean up the image after tests
        try:
            subprocess.run(
                ["docker", "rmi", image_name],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, Exception):
            pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def docker_container(docker_image: str) -> Generator[Dict[str, Any], None, None]:
    """Run a Docker container for testing."""
    container_name = "vits-tts-test-container"
    
    try:
        # Run the container
        process = subprocess.Popen([
            "docker", "run", "--name", container_name,
            "-p", "8888:8888",
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
                response = requests.get("http://localhost:8888/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                if i == max_retries - 1:
                    pytest.fail("Service did not become ready in time")
                time.sleep(2)
        
        yield {
            "name": container_name,
            "host": "localhost",
            "port": 888
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


@pytest.fixture(scope="function")
def docker_container_infore_model(docker_image: str) -> Generator[Dict[str, Any], None, None]:
    """Run a Docker container with InfoRE model for testing."""
    container_name = "vits-tts-test-container-infore"
    
    try:
        # Run the container with InfoRE model
        process = subprocess.Popen([
            "docker", "run", "--name", container_name,
            "-p", "8889:8888",
            "-e", "TTS_MODEL_PATH=models/infore/vi_VN-vais1000-medium.onnx",
            "-e", "TTS_CONFIG_PATH=models/infore/vi_VN-vais1000-medium.onnx.json",
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
                response = requests.get("http://localhost:8889/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                if i == max_retries - 1:
                    pytest.fail("Service did not become ready in time")
                time.sleep(2)
        
        yield {
            "name": container_name,
            "host": "localhost",
            "port": 8889
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


@pytest.fixture(scope="function")
def docker_container_v2_model(docker_image: str) -> Generator[Dict[str, Any], None, None]:
    """Run a Docker container with V2 model for testing."""
    container_name = "vits-tts-test-container-v2"
    
    try:
        # Run the container with V2 model (default)
        process = subprocess.Popen([
            "docker", "run", "--name", container_name,
            "-p", "8890:8888",
            "-e", "TTS_MODEL_PATH=models/v2/finetuning_pretrained_vi.onnx",
            "-e", "TTS_CONFIG_PATH=models/v2/finetuning_pretrained_vi.onnx.json",
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
                response = requests.get("http://localhost:8890/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                if i == max_retries - 1:
                    pytest.fail("Service did not become ready in time")
                time.sleep(2)
        
        yield {
            "name": container_name,
            "host": "localhost",
            "port": 8890
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