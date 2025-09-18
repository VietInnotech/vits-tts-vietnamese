"""API routers for TTS endpoints.

Provides controller-based route handlers for file-based and streaming TTS.
"""

from litestar import Controller, get
from litestar.response import Stream, Redirect

from ..core.tts_service import TTSService
from .schemas import TTSResponse


class TTSController(Controller):
    """Controller exposing /tts endpoints.

    This controller provides two endpoints:
      - GET /tts: Synthesize text to a file and return metadata including an audio URL.
      - GET /tts/stream: Stream synthesized audio as WAV bytes.

    Endpoints accept primitive query parameters (text, speed) and rely on an
    injected TTSService (dependency name: "service").
    """

    path = "/tts"

    @get()
    async def generate_tts(self, service: TTSService, text: str, speed: str = "normal") -> TTSResponse:
        """Generate a file-based TTS result.

        Args:
            service: Injected TTSService instance.
            text: Text to synthesize.
            speed: Speech speed label.

        Returns:
            TTSResponse: Metadata including hash, text, speed and audio_url.
        """
        result = await service.handle_tts_request(text, speed)
        # Return file path for generated audio; UI/static serving removed.
        audio_url = f"/audio/{result['file_name']}"
        return TTSResponse(hash=result["hash"], text=result["text"], speed=result["speed"], audio_url=audio_url)

    @get("/stream")
    async def stream_tts(self, service: TTSService, text: str, speed: str = "normal") -> Stream:
        """Stream synthesized audio as WAV.

        Args:
            service: Injected TTSService instance.
            text: Text to synthesize.
            speed: Speech speed label.

        Returns:
            Stream: A litestar Stream that yields WAV bytes with media_type "audio/wav".
        """
        audio_gen = await service.handle_tts_streaming_request(text, speed)
        return Stream(audio_gen, media_type="audio/wav")


class RootController(Controller):
    """Controller for root endpoint."""

    path = "/"

    @get()
    async def redirect_to_docs(self) -> Redirect:
        """Redirect to the Swagger UI documentation."""
        return Redirect(path="/docs")