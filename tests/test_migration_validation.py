"""Validation test for migrated LiteStar API endpoints."""
from litestar.testing import create_test_client
from src.vits_tts.app import create_app


def test_migration_validation():
    """Validation test for migrated LiteStar API endpoints."""
    app = create_app()
    with create_test_client(app) as client:
        # Test the GET /tts endpoint
        response = client.get("/tts", params={"text": "Hello world", "speed": "normal"})
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        if response.status_code != 200:
            print(f"Response headers: {dict(response.headers)}")
        assert response.status_code == 200
        data = response.json()
        assert "hash" in data
        assert "text" in data
        assert "speed" in data
        assert "audio_url" in data
        assert data["text"] == "Hello world"
        assert data["speed"] == "normal"

        # Test the streaming endpoint
        response = client.get("/tts/stream", params={"text": "Hello streaming", "speed": "fast"})
        print(f"Stream response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Stream response content: {response.text}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"