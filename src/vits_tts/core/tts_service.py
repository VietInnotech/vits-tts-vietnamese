"""TTS service layer.

This module provides the TTSService which handles caching and delegates
text-to-speech synthesis to the injected PiperTTS implementation.
"""

import hashlib
import os
from io import BytesIO
from pathlib import Path
from typing import AsyncGenerator

from cachetools import LRUCache

from ..tts import PiperTTS


class TTSService:
    """Service responsible for generating and caching TTS audio.

    Attributes:
        cache (LRUCache): In-memory LRU cache for audio artifacts.
        config (dict): Application configuration dictionary.
        audio_output_dir (str): Directory to store generated audio files.
        model (PiperTTS): Injected PiperTTS instance used for synthesis.
    """

    def __init__(self, cache: LRUCache, config: dict, model: PiperTTS):
        """Initialize the TTSService.

        Args:
            cache: An LRUCache instance used to store generated audio markers or buffers.
            config: Application configuration dictionary (may be empty).
            model: An instance of PiperTTS used to perform synthesis.
        """
        # cache for audio artifacts
        self.cache = cache
        # application config
        self.config = config or {}
        self.audio_output_dir = self.config.get("tts", {}).get("audio_output_dir", "audio/")
        # injected PiperTTS instance (keeps unpickleable objects out of app.state)
        self.model = model

    async def handle_tts_request(self, text: str, speed: str) -> dict:
        """Handle file-based TTS request.

        Synthesize audio to a file if not cached, and return metadata describing
        the generated (or cached) artifact.

        Args:
            text: Text to synthesize.
            speed: Speech speed label.

        Returns:
            dict: Contains keys "hash", "text", "speed", and "file_name".
        """
        text_hash = hashlib.sha1((text + speed).encode("utf-8")).hexdigest()
        file_name = f"{text_hash}.wav"
        file_path = Path(os.getcwd()) / self.audio_output_dir / file_name

        cache_key = f"file:{text_hash}"

        # memory cache hit
        if cache_key in self.cache:
            return {"hash": text_hash, "text": text, "speed": speed, "file_name": file_name}

        # filesystem cache hit
        if file_path.is_file():
            # store a lightweight marker in memory cache
            self.cache[cache_key] = True
            return {"hash": text_hash, "text": text, "speed": speed, "file_name": file_name}

        # generate audio and save file using injected model
        output_path = str(Path(self.audio_output_dir) / file_name)
        self.model.text_to_speech(text, speed, output_path)
        # mark cached
        self.cache[cache_key] = True

        return {"hash": text_hash, "text": text, "speed": speed, "file_name": file_name}

    async def handle_tts_streaming_request(self, text: str, speed: str) -> AsyncGenerator[bytes, None]:
        """Handle streaming TTS requests.

        Returns an async generator that yields audio bytes for streaming endpoints.

        Args:
            text: Text to synthesize.
            speed: Speech speed label.

        Returns:
            AsyncGenerator[bytes, None]: Generator that yields audio bytes in chunks.
        """
        cache_key = f"stream:{hashlib.sha1((text + speed).encode('utf-8')).hexdigest()}"

        if cache_key in self.cache:
            audio_buffer: BytesIO = self.cache[cache_key]
            audio_buffer.seek(0)
        else:
            audio_buffer = self.model.text_to_speech_streaming(text, speed)
            audio_buffer.seek(0)
            self.cache[cache_key] = audio_buffer

        chunk_size = 8192

        async def _gen():
            while True:
                chunk = audio_buffer.read(chunk_size)
                if not chunk:
                    break
                yield chunk

        return _gen()