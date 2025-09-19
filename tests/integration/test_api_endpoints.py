"""Integration tests for API endpoints running in Docker containers."""

import requests
import pytest
from typing import Dict, Any


def test_health_endpoint(docker_container: Dict[str, Any]) -> None:
    """Test that the health endpoint returns 200 OK."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/health"
    response = requests.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "message" in data
    assert "TTS service is running" in data["message"]


def test_tts_endpoint(docker_container: Dict[str, Any]) -> None:
    """Test that the TTS endpoint generates audio and returns metadata."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    params = {
        "text": "Xin chào Việt Nam!",
        "speed": "normal"
    }
    
    response = requests.get(url, params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "hash" in data
    assert "text" in data
    assert "speed" in data
    assert "audio_url" in data
    
    # Verify values
    assert data["text"] == "Xin chào Việt Nam!"
    assert data["speed"] == "normal"
    assert data["audio_url"].startswith("/audio/")
    assert data["audio_url"].endswith(".wav")


def test_tts_streaming_endpoint(docker_container: Dict[str, Any]) -> None:
    """Test that the TTS streaming endpoint returns audio data."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts/stream"
    params = {
        "text": "Chào mừng bạn đến với dịch vụ TTS!",
        "speed": "normal"
    }
    
    response = requests.get(url, params=params)
    
    assert response.status_code == 200
    assert response.headers.get("content-type") == "audio/wav"
    
    # Verify we got audio data
    audio_data = response.content
    assert len(audio_data) > 0
    
    # Verify it's a valid WAV file (starts with RIFF header)
    assert audio_data.startswith(b"RIFF")


def test_different_speeds(docker_container: Dict[str, Any]) -> None:
    """Test that different speed parameters work."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    text = "Kiểm tra tốc độ phát âm"
    
    for speed in ["slow", "normal", "fast"]:
        params = {
            "text": text,
            "speed": speed
        }
        
        response = requests.get(url, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data["speed"] == speed


def test_vietnamese_text_handling(docker_container: Dict[str, Any]) -> None:
    """Test handling of Vietnamese text with diacritics."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    
    vietnamese_texts = [
        "Xin chào thế giới",
        "Cảm ơn bạn rất nhiều",
        "Tôi yêu Việt Nam",
        "Hà Nội là thủ đô của Việt Nam"
    ]
    
    for text in vietnamese_texts:
        params = {
            "text": text,
            "speed": "normal"
        }
        
        response = requests.get(url, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == text


def test_audio_file_serving(docker_container: Dict[str, Any]) -> None:
    """Test that generated audio files are accessible via /audio endpoint."""
    # First generate an audio file
    tts_url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    params = {
        "text": "Kiểm tra việc phục vụ tệp âm thanh",
        "speed": "normal"
    }
    
    tts_response = requests.get(tts_url, params=params)
    assert tts_response.status_code == 200
    
    tts_data = tts_response.json()
    audio_url = tts_data["audio_url"]
    
    # Now try to access the audio file directly
    full_audio_url = f"http://{docker_container['host']}:{docker_container['port']}{audio_url}"
    audio_response = requests.get(full_audio_url)
    
    # Should return the audio file
    assert audio_response.status_code == 200
    # Accept both audio/wav and audio/x-wav as both are valid MIME types for WAV files
    content_type = audio_response.headers.get("content-type", "")
    assert content_type in ["audio/wav", "audio/x-wav"], f"Unexpected content-type: {content_type}"
    assert len(audio_response.content) > 0


def test_error_handling_empty_text(docker_container: Dict[str, Any]) -> None:
    """Test error handling for empty text."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    params = {
        "text": "",
        "speed": "normal"
    }
    
    response = requests.get(url, params=params)
    
    # Should either succeed with empty audio or return appropriate error
    assert response.status_code in [200, 400, 422]


def test_special_characters_handling(docker_container: Dict[str, Any]) -> None:
    """Test handling of special characters and Vietnamese text."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    
    special_texts = [
        "Xin chào! Có dấu tiếng Việt.",
        "Numbers 123 and symbols !@#$%",
        "Unicode: 你好 🌍 مرحبا"
    ]
    
    for text in special_texts:
        params = {
            "text": text,
            "speed": "normal"
        }
        
        response = requests.get(url, params=params)
        
        # Should handle special characters gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == text


def test_docs_endpoint(docker_container: Dict[str, Any]) -> None:
    """Test that the docs endpoint is accessible."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/docs"
    response = requests.get(url)
    
    # Should return the API documentation
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_root_redirect(docker_container: Dict[str, Any]) -> None:
    """Test that the root endpoint redirects to docs."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/"
    response = requests.get(url, allow_redirects=False)
    
    # Should redirect to /docs
    assert response.status_code == 307  # Temporary redirect
    assert "location" in response.headers
    assert response.headers["location"] == "/docs"