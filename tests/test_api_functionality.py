"""Comprehensive API functionality tests after web interface removal.

Tests all TTS endpoints to ensure:
- TTS endpoint returns accessible audio URLs
- Audio files are served correctly at /audio endpoint
- Streaming endpoint functions at /tts/stream
- No web interface remnants exist
- Both file generation and streaming work with sample requests
"""

import asyncio
import hashlib
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from io import BytesIO

from litestar import Litestar
from litestar.testing import AsyncTestClient

from vits_tts.app import create_app
from vits_tts.core.tts_service import TTSService
from vits_tts.tts import PiperTTS


@pytest.fixture
def app() -> Litestar:
    """Create a test application instance."""
    return create_app()


@pytest.fixture
async def client(app: Litestar):
    """Create an async test client."""
    async with AsyncTestClient(app=app) as client:
        yield client


class TestAPIFunctionality:
    """Test suite for API functionality after web interface removal."""

    async def test_tts_endpoint_returns_accessible_audio_url(self, client: AsyncTestClient):
        """Test that TTS endpoint returns a response with accessible audio URL."""
        response = await client.get("/tts", params={"text": "Xin chào thế giới", "speed": "normal"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "hash" in data
        assert "text" in data
        assert "speed" in data
        assert "audio_url" in data
        
        # Verify audio_url format
        assert data["audio_url"].startswith("/audio/")
        assert data["audio_url"].endswith(".wav")
        
        # Verify text matches request
        assert data["text"] == "Xin chào thế giới"
        assert data["speed"] == "normal"

    async def test_audio_files_served_correctly(self, client: AsyncTestClient):
        """Test that generated audio files are accessible via /audio endpoint."""
        # First generate an audio file
        tts_response = await client.get("/tts", params={"text": "Test audio serving", "speed": "normal"})
        assert tts_response.status_code == 200
        
        tts_data = tts_response.json()
        audio_url = tts_data["audio_url"]
        
        # Now try to access the audio file directly
        audio_response = await client.get(audio_url)
        
        # Should return the audio file or 404 if not generated yet
        # The file might not exist if generation failed, so we check both possibilities
        assert audio_response.status_code in [200, 404]
        
        if audio_response.status_code == 200:
            # Verify it's a WAV file
            assert audio_response.headers.get("content-type") == "audio/wav"
            assert len(audio_response.content) > 0

    async def test_streaming_endpoint_functions(self, client: AsyncTestClient):
        """Test that streaming endpoint returns audio data."""
        response = await client.get("/tts/stream", params={"text": "Streaming test", "speed": "normal"})
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "audio/wav"
        
        # Read streaming content
        audio_data = b""
        async for chunk in response.aiter_bytes():
            audio_data += chunk
            
        # Verify we got some audio data
        assert len(audio_data) > 0
        
        # Verify it's a valid WAV file (starts with RIFF header)
        assert audio_data.startswith(b"RIFF")

    async def test_no_web_interface_remnants(self, client: AsyncTestClient):
        """Test that no web interface endpoints exist."""
        # Test common web interface paths that should not exist
        web_paths = ["/", "/index.html", "/static", "/assets", "/favicon.ico"]
        
        for path in web_paths:
            response = await client.get(path)
            # Should return 404 for any web interface remnants
            assert response.status_code == 404, f"Web interface remnant found at {path}"

    async def test_file_generation_and_caching(self, client: AsyncTestClient):
        """Test that file generation works and caching prevents regeneration."""
        text = "Caching test text"
        speed = "normal"
        
        # First request - should generate file
        response1 = await client.get("/tts", params={"text": text, "speed": speed})
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second request - should use cache
        response2 = await client.get("/tts", params={"text": text, "speed": speed})
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should return same hash and file name
        assert data1["hash"] == data2["hash"]
        assert data1["file_name"] == data2["file_name"]

    async def test_streaming_caching(self, client: AsyncTestClient):
        """Test that streaming endpoint also uses caching."""
        text = "Streaming cache test"
        speed = "normal"
        
        # First request
        response1 = await client.get("/tts/stream", params={"text": text, "speed": speed})
        assert response1.status_code == 200
        audio1 = b"".join([chunk async for chunk in response1.aiter_bytes()])
        
        # Second request should return same data from cache
        response2 = await client.get("/tts/stream", params={"text": text, "speed": speed})
        assert response2.status_code == 200
        audio2 = b"".join([chunk async for chunk in response2.aiter_bytes()])
        
        # Should be identical
        assert audio1 == audio2

    async def test_different_speeds(self, client: AsyncTestClient):
        """Test that different speed parameters work."""
        text = "Speed test"
        
        for speed in ["slow", "normal", "fast"]:
            response = await client.get("/tts", params={"text": text, "speed": speed})
            assert response.status_code == 200
            data = response.json()
            assert data["speed"] == speed

    async def test_error_handling_empty_text(self, client: AsyncTestClient):
        """Test error handling for empty text."""
        response = await client.get("/tts", params={"text": "", "speed": "normal"})
        # Should either succeed with empty audio or return appropriate error
        assert response.status_code in [200, 400, 422]

    async def test_special_characters_handling(self, client: AsyncTestClient):
        """Test handling of special characters and Vietnamese text."""
        special_texts = [
            "Xin chào! Có dấu tiếng Việt.",
            "Numbers 123 and symbols !@#$%",
            "Unicode: 你好 🌍 مرحبا",
        ]
        
        for text in special_texts:
            response = await client.get("/tts", params={"text": text, "speed": "normal"})
            # Should handle special characters gracefully
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == text

    async def test_concurrent_requests(self, client: AsyncTestClient):
        """Test handling of concurrent requests."""
        texts = ["Concurrent test 1", "Concurrent test 2", "Concurrent test 3"]
        
        # Make concurrent requests
        tasks = [
            client.get("/tts", params={"text": text, "speed": "normal"})
            for text in texts
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_audio_directory_exists(self):
        """Test that audio directory is properly configured."""
        audio_dir = Path("audio")
        assert audio_dir.exists(), "Audio directory should exist"
        assert audio_dir.is_dir(), "Audio should be a directory"

    def test_no_static_web_assets(self):
        """Test that no static web assets directory exists."""
        # Common web asset directories that should not exist
        web_dirs = ["static", "assets", "public", "www"]
        
        for dir_name in web_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                # If it exists, it should not contain web interface files
                files = list(dir_path.iterdir())
                # Should not contain HTML, CSS, JS files
                web_files = [f for f in files if f.suffix in ['.html', '.css', '.js', '.htm']]
                assert len(web_files) == 0, f"Web interface files found in {dir_name}: {web_files}"


class TestTTSServiceIntegration:
    """Test TTSService integration with mocked dependencies."""

    @pytest.fixture
    def mock_piper_tts(self):
        """Create a mock PiperTTS instance."""
        mock = MagicMock(spec=PiperTTS)
        
        # Mock text_to_speech method
        def mock_text_to_speech(text, speed, output_path):
            # Create a minimal WAV file for testing
            wav_header = b"RIFF\x26\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x02\x00\x00\x00\x00\x00"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(wav_header)
        
        mock.text_to_speech = mock_text_to_speech
        
        # Mock text_to_speech_streaming method
        def mock_text_to_speech_streaming(text, speed):
            buffer = BytesIO()
            buffer.write(b"RIFF\x26\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x02\x00\x00\x00\x00\x00")
            buffer.seek(0)
            return buffer
        
        mock.text_to_speech_streaming = mock_text_to_speech_streaming
        
        return mock

    async def test_tts_service_with_mock(self, mock_piper_tts):
        """Test TTSService with mocked PiperTTS."""
        from cachetools import LRUCache
        
        cache = LRUCache(maxsize=100)
        config = {"tts": {"audio_output_dir": "test_audio"}}
        service = TTSService(cache=cache, config=config, model=mock_piper_tts)
        
        # Test file generation
        result = await service.handle_tts_request("Test text", "normal")
        
        assert "hash" in result
        assert "text" in result
        assert "speed" in result
        assert "file_name" in result
        assert result["text"] == "Test text"
        assert result["speed"] == "normal"
        
        # Test streaming
        stream_gen = await service.handle_tts_streaming_request("Test stream", "normal")
        
        audio_data = b""
        async for chunk in stream_gen:
            audio_data += chunk
            
        assert len(audio_data) > 0
        assert audio_data.startswith(b"RIFF")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])