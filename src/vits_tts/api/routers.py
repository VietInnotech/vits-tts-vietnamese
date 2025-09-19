"""API routers for TTS endpoints.

Provides controller-based route handlers for file-based and streaming TTS.
"""

from litestar import Controller, get
from litestar.response import Stream, Redirect, File
from litestar.enums import MediaType
from litestar.exceptions import HTTPException
from typing import Dict, Any
from litestar.status_codes import HTTP_307_TEMPORARY_REDIRECT
from pathlib import Path

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
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Streaming TTS for text: '{text}' with speed: '{speed}'")
            audio_gen = await service.handle_tts_streaming_request(text, speed)
            logger.info("TTS streaming generation successful")
            return Stream(audio_gen, media_type="audio/wav")
        except Exception as e:
            logger.error(f"TTS streaming generation failed: {str(e)}", exc_info=True)
            from litestar.exceptions import HTTPException
            raise HTTPException(status_code=500, detail=f"TTS streaming generation failed: {str(e)}")


class RootController(Controller):
    """Controller for root endpoint."""

    path = "/"

    @get()
    async def redirect_to_docs(self) -> Redirect:
        """Redirect to the Swagger UI documentation."""
        return Redirect(path="/docs", status_code=HTTP_307_TEMPORARY_REDIRECT)
    
    @get("/health")
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint.
        
        Returns:
            Dict[str, Any]: Health status information.
        """
        return {"status": "healthy", "message": "TTS service is running"}
