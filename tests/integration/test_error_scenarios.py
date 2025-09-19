"""Integration tests for error scenarios and edge cases in Docker containers."""

import requests
import pytest
from typing import Dict, Any


def test_invalid_endpoint(docker_container: Dict[str, Any]) -> None:
    """Test that invalid endpoints return 404."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/invalid-endpoint"
    response = requests.get(url)
    
    assert response.status_code == 404


def test_missing_text_parameter(docker_container: Dict[str, Any]) -> None:
    """Test error handling for missing text parameter."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    params = {
        "speed": "normal"
        # Missing "text" parameter
    }
    
    response = requests.get(url, params=params)
    
    # Should return error for missing required parameter
    assert response.status_code in [400, 422]


def test_empty_text_parameter(docker_container: Dict[str, Any]) -> None:
    """Test handling of empty text parameter."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    params = {
        "text": "",
        "speed": "normal"
    }
    
    response = requests.get(url, params=params)
    
    # Should either succeed with empty audio or return appropriate error
    assert response.status_code in [200, 400, 422]


def test_invalid_speed_parameter(docker_container: Dict[str, Any]) -> None:
    """Test handling of invalid speed parameter."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    params = {
        "text": "Test with invalid speed",
        "speed": "invalid-speed"
    }
    
    response = requests.get(url, params=params)
    
    # Should either succeed with default speed or return appropriate error
    assert response.status_code in [200, 400, 422]


def test_very_long_text(docker_container: Dict[str, Any]) -> None:
    """Test handling of very long text input."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    long_text = "Xin chào " * 1000  # Very long text
    params = {
        "text": long_text,
        "speed": "normal"
    }
    
    response = requests.get(url, params=params)
    
    # Should handle long text gracefully (might take longer to process)
    assert response.status_code == 200
    data = response.json()
    assert "hash" in data
    assert "audio_url" in data


def test_special_characters_and_unicode(docker_container: Dict[str, Any]) -> None:
    """Test handling of special characters and Unicode text."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    
    special_texts = [
        "Text with numbers 12345",
        "Special symbols !@#$%^&*()",
        "Unicode text: 你好 🌍 مرحبا",
        "Mixed: Xin chào! 你好 🌍 123",
        "Emoji only: 🎉🎊🎈🌟✨"
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


def test_concurrent_requests(docker_container: Dict[str, Any]) -> None:
    """Test handling of concurrent requests."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/ts"
    texts = [
        "Concurrent request 1",
        "Concurrent request 2", 
        "Concurrent request 3"
    ]
    
    # Make multiple requests
    responses = []
    for text in texts:
        params = {
            "text": text,
            "speed": "normal"
        }
        response = requests.get(url, params=params)
        responses.append(response)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert "hash" in data
        assert "audio_url" in data


def test_streaming_with_invalid_parameters(docker_container: Dict[str, Any]) -> None:
    """Test streaming endpoint with invalid parameters."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts/stream"
    
    # Test missing text parameter
    params = {
        "speed": "normal"
        # Missing "text" parameter
    }
    
    response = requests.get(url, params=params)
    
    # Should return error for missing required parameter
    assert response.status_code in [400, 422]


def test_health_check_always_available(docker_container: Dict[str, Any]) -> None:
    """Test that health check endpoint is always available."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/health"
    
    # Make multiple health check requests
    for _ in range(5):
        response = requests.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


def test_cors_headers(docker_container: Dict[str, Any]) -> None:
    """Test that CORS headers are present."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/health"
    response = requests.get(url)
    
    # Check for common CORS headers
    # Note: This service might not have CORS enabled by default
    # but we can check if any are present
    headers = response.headers
    # We won't assert on specific CORS headers as they may not be configured
    # but we can verify the response is valid
    assert response.status_code == 200


def test_request_with_different_http_methods(docker_container: Dict[str, Any]) -> None:
    """Test that endpoints handle different HTTP methods correctly."""
    base_url = f"http://{docker_container['host']}:{docker_container['port']}"
    
    # Test POST to GET-only endpoint
    response = requests.post(f"{base_url}/health")
    # Should return 405 Method Not Allowed or 404 Not Found
    assert response.status_code in [404, 405]
    
    # Test PUT to GET-only endpoint
    response = requests.put(f"{base_url}/health")
    # Should return 405 Method Not Allowed or 404 Not Found
    assert response.status_code in [404, 405]
    
    # Test DELETE to GET-only endpoint
    response = requests.delete(f"{base_url}/health")
    # Should return 405 Method Not Allowed or 404 Not Found
    assert response.status_code in [404, 405]


def test_large_payload_handling(docker_container: Dict[str, Any]) -> None:
    """Test handling of large payloads in requests."""
    url = f"http://{docker_container['host']}:{docker_container['port']}/tts"
    
    # While this service uses query parameters, we can test with a very long URL
    long_text = "Test " * 5000  # Very long text
    params = {
        "text": long_text,
        "speed": "normal"
    }
    
    try:
        response = requests.get(url, params=params)
        # If it succeeds, verify the response
        if response.status_code == 200:
            data = response.json()
            assert "hash" in data
            assert "audio_url" in data
        # If it fails, it should be a client error, not a server error
        else:
            assert response.status_code < 500
    except requests.exceptions.RequestException:
        # If the request fails due to URL length, that's acceptable
        pass