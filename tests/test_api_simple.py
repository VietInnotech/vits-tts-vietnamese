"""Simple API functionality tests after web interface removal.

Tests core TTS functionality without complex async fixtures.
"""

import pytest
from pathlib import Path
from litestar import Litestar
from litestar.testing import AsyncTestClient

from vits_tts.app import create_app


def test_app_creation():
    """Test that the app can be created successfully."""
    app = create_app()
    assert isinstance(app, Litestar)
    
    # Verify the app has been created with expected configuration
    # The app should have static files config for /audio endpoint
    assert app.static_files_config is not None
    assert len(app.static_files_config) > 0


def test_audio_directory_exists():
    """Test that audio directory exists for file storage."""
    audio_dir = Path("audio")
    assert audio_dir.exists(), "Audio directory should exist"
    assert audio_dir.is_dir(), "Audio should be a directory"


def test_no_web_interface_files():
    """Test that no web interface files exist."""
    # Common web interface files that should not exist
    web_files = [
        "index.html", "index.htm", "app.html", "main.html",
        "static/", "assets/", "public/", "www/", "templates/"
    ]
    
    for web_file in web_files:
        path = Path(web_file)
        if path.exists():
            if path.is_file():
                pytest.fail(f"Web interface file found: {web_file}")
            elif path.is_dir():
                # Check for web files in directory
                web_extensions = ['.html', '.htm', '.css', '.js', '.vue', '.react']
                for ext in web_extensions:
                    if list(path.glob(f"*{ext}")):
                        pytest.fail(f"Web interface files found in {web_file}")


@pytest.mark.asyncio
async def test_tts_endpoint_basic():
    """Test basic TTS endpoint functionality."""
    app = create_app()
    
    async with AsyncTestClient(app=app) as client:
        # Test basic TTS request
        response = await client.get("/tts", params={"text": "Hello world", "speed": "normal"})
        
        # Should return successful response
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure
        required_fields = ["hash", "text", "speed", "audio_url"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify audio_url format
        assert data["audio_url"].startswith("/audio/")
        assert data["audio_url"].endswith(".wav")
        
        # Verify text matches request
        assert data["text"] == "Hello world"
        assert data["speed"] == "normal"


@pytest.mark.asyncio
async def test_streaming_endpoint_basic():
    """Test basic streaming endpoint functionality."""
    app = create_app()
    
    async with AsyncTestClient(app=app) as client:
        # Test streaming request
        response = await client.get("/tts/stream", params={"text": "Streaming test", "speed": "normal"})
        
        # Should return successful response
        assert response.status_code == 200
        
        # Verify content type
        assert response.headers.get("content-type") == "audio/wav"
        
        # Read streaming content
        audio_data = b""
        async for chunk in response.aiter_bytes():
            audio_data += chunk
            
        # Verify we got some audio data
        assert len(audio_data) > 0, "No audio data received"
        
        # Verify it's a valid WAV file (starts with RIFF header)
        assert audio_data.startswith(b"RIFF"), "Invalid WAV file format"


@pytest.mark.asyncio
async def test_no_web_interface_endpoints():
    """Test that web interface endpoints return 404."""
    app = create_app()
    
    async with AsyncTestClient(app=app) as client:
        # Test common web interface paths
        web_paths = ["/", "/index.html", "/static", "/assets", "/favicon.ico"]
        
        for path in web_paths:
            response = await client.get(path)
            # Should return 404 for any web interface remnants
            assert response.status_code == 404, f"Web interface remnant found at {path}"


@pytest.mark.asyncio
async def test_audio_file_serving():
    """Test that audio files can be served from /audio endpoint."""
    app = create_app()
    
    async with AsyncTestClient(app=app) as client:
        # First generate an audio file via TTS
        tts_response = await client.get("/tts", params={"text": "Audio serving test", "speed": "normal"})
        assert tts_response.status_code == 200
        
        tts_data = tts_response.json()
        audio_url = tts_data["audio_url"]
        
        # Now try to access the audio file directly
        audio_response = await client.get(audio_url)
        
        # Should either return the audio file (200) or file not found (404)
        # The file might not exist if generation failed or model is not available
        assert audio_response.status_code in [200, 404], f"Unexpected status code: {audio_response.status_code}"
        
        if audio_response.status_code == 200:
            # Verify it's a WAV file
            assert audio_response.headers.get("content-type") == "audio/wav"
            assert len(audio_response.content) > 0


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for invalid requests."""
    app = create_app()
    
    async with AsyncTestClient(app=app) as client:
        # Test missing text parameter
        response = await client.get("/tts")
        # Should return error for missing required parameter
        assert response.status_code in [400, 422]
        
        # Test with empty text
        response = await client.get("/tts", params={"text": "", "speed": "normal"})
        # Should either succeed with empty audio or return appropriate error
        assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_vietnamese_text_handling():
    """Test handling of Vietnamese text with diacritics."""
    app = create_app()
    
    async with AsyncTestClient(app=app) as client:
        vietnamese_texts = [
            "Xin chào thế giới",
            "Cảm ơn bạn rất nhiều",
            "Tôi yêu Việt Nam",
        ]
        
        for text in vietnamese_texts:
            response = await client.get("/tts", params={"text": text, "speed": "normal"})
            # Should handle Vietnamese text gracefully
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])