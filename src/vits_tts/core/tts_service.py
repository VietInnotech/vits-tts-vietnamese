"""TTS service layer with enhanced Docker compatibility.

This module provides the TTSService which handles caching and delegates
text-to-speech synthesis to the injected PiperTTS implementation, with
comprehensive error handling and diagnostic logging for Docker environments.
"""

import hashlib
import os
import logging
from io import BytesIO
from pathlib import Path
from typing import AsyncGenerator

from cachetools import LRUCache

from ..tts import PiperTTS


class TTSService:
    """Service responsible for generating and caching TTS audio with Docker compatibility.

    Attributes:
        cache (LRUCache): In-memory LRU cache for audio artifacts.
        config (dict): Application configuration dictionary.
        audio_output_dir (str): Directory to store generated audio files.
        model (PiperTTS): Injected PiperTTS instance used for synthesis.
    """

    def __init__(self, cache: LRUCache, config: dict, model: PiperTTS):
        """Initialize the TTSService with Docker compatibility.

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
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"TTSService initialized with audio_output_dir: {self.audio_output_dir}")

    async def handle_tts_request(self, text: str, speed: str) -> dict:
        """Handle file-based TTS request with Docker compatibility.

        Synthesize audio to a file if not cached, and return metadata describing
        the generated (or cached) artifact.

        Args:
            text: Text to synthesize.
            speed: Speech speed label.

        Returns:
            dict: Contains keys "hash", "text", "speed", and "file_name".

        Raises:
            ValueError: If text is empty, invalid, or if there are permission/file system issues
        """
        self.logger.info(f"Docker-enhanced TTS request: text='{text}', speed='{speed}'")
        
        try:
            # Validate input parameters with enhanced logging
            if not text or not text.strip():
                self.logger.error("Text parameter is empty or contains only whitespace")
                raise ValueError("Text parameter cannot be empty")
            
            if not speed:
                speed = "normal"
                self.logger.debug(f"Speed parameter not provided, using default: {speed}")
            
            # Validate speed parameter with better logging
            valid_speeds = ["very_slow", "slow", "normal", "fast", "very_fast"]
            if speed not in valid_speeds:
                # Try to map common variations
                speed_mapping = {
                    "slow": "slow",
                    "normal": "normal", 
                    "fast": "fast",
                    "very_slow": "very_slow",
                    "very_fast": "very_fast"
                }
                if speed in speed_mapping:
                    mapped_speed = speed_mapping[speed]
                    self.logger.debug(f"Mapped speed '{speed}' to '{mapped_speed}'")
                    speed = mapped_speed
                else:
                    # Default to normal for invalid speeds
                    self.logger.warning(f"Invalid speed '{speed}', defaulting to 'normal'")
                    speed = "normal"

            # Validate text length (prevent memory issues)
            max_text_length = 10000
            if len(text) > max_text_length:
                self.logger.error(f"Text too long: {len(text)} characters (max: {max_text_length})")
                raise ValueError(f"Text too long. Maximum length is {max_text_length} characters")

            # Generate hash and file name
            text_hash = hashlib.sha1((text + speed).encode("utf-8")).hexdigest()
            file_name = f"{text_hash}.wav"
            
            self.logger.debug(f"Generated file name: {file_name}, hash: {text_hash}")

            # Check memory cache
            cache_key = f"file:{text_hash}"
            if cache_key in self.cache:
                self.logger.info(f"Cache hit for key: {cache_key}")
                return {"hash": text_hash, "text": text, "speed": speed, "file_name": file_name}

            # Check filesystem cache
            file_path = Path(self.audio_output_dir) / file_name
            if file_path.is_file():
                self.logger.info(f"Filesystem cache hit for file: {file_path}")
                self.cache[cache_key] = True
                return {"hash": text_hash, "text": text, "speed": speed, "file_name": file_name}

            self.logger.info(f"Cache miss, generating new audio file: {file_name}")

            # Enhanced directory and permission handling
            output_dir = Path(self.audio_output_dir)
            self.logger.debug(f"Ensuring output directory exists: {output_dir}")
            
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Output directory created/exists: {output_dir}")
            except Exception as dir_error:
                self.logger.error(f"Failed to create output directory {output_dir}: {dir_error}")
                raise ValueError(f"Cannot create audio output directory: {dir_error}")
            
            # Verify write permissions by testing file creation
            try:
                test_file = output_dir / ".permission_test"
                test_file.touch()
                test_file.unlink()
                self.logger.debug("Write permissions verified for output directory")
            except Exception as perm_error:
                self.logger.error(f"Write permissions test failed for {output_dir}: {perm_error}")
                self.logger.error(f"Directory permissions: {oct(output_dir.stat().st_mode) if output_dir.exists() else 'N/A'}")
                self.logger.error(f"Current user: {os.getenv('USER', 'unknown')}")
                self.logger.error(f"Working directory: {os.getcwd()}")
                self.logger.error(f"Audio output directory config: {self.audio_output_dir}")
                raise ValueError(f"Insufficient permissions to write to audio directory: {perm_error}")
            
            # Generate audio using the model
            self.logger.debug(f"Calling model.text_to_speech with output_path: {file_path}")
            result_path = self.model.text_to_speech(text, speed, str(file_path))
            self.logger.info(f"TTS synthesis completed successfully, result_path: {result_path}")
            
            # Verify the file was created
            result_path_obj = Path(result_path)
            if result_path_obj.exists():
                file_size = result_path_obj.stat().st_size
                self.logger.info(f"Audio file created successfully: {result_path}, size: {file_size} bytes")
            else:
                self.logger.error(f"Audio file was not created at expected path: {result_path}")
                raise ValueError(f"Audio file generation failed - no file created at {result_path}")
            
            # Mark as cached
            self.cache[cache_key] = True
            self.logger.info(f"Audio generation successful, cached with key: {cache_key}")

            return {"hash": text_hash, "text": text, "speed": speed, "file_name": file_name}
                
        except ValueError as e:
            # Re-raise validation errors from the model
            self.logger.error(f"Validation error in TTS synthesis: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            # Log and re-wrap unexpected errors with full context
            self.logger.error(f"TTS synthesis failed with unexpected error: {str(e)}", exc_info=True)
            self.logger.error(f"Error context: audio_output_dir='{self.audio_output_dir}'")
            raise ValueError(f"Failed to synthesize audio: {str(e)}")

    async def handle_tts_streaming_request(self, text: str, speed: str) -> AsyncGenerator[bytes, None]:
        """Handle streaming TTS requests with enhanced error handling.

        Returns an async generator that yields audio bytes for streaming endpoints.

        Args:
            text: Text to synthesize.
            speed: Speech speed label.

        Returns:
            AsyncGenerator[bytes, None]: Generator that yields audio bytes in chunks.

        Raises:
            ValueError: If text is empty or invalid
        """
        self.logger.info(f"Docker-enhanced streaming TTS request: text='{text}', speed='{speed}'")
        
        # Validate input parameters
        if not text or not text.strip():
            self.logger.error("Text parameter is empty or contains only whitespace")
            raise ValueError("Text parameter cannot be empty")
        
        if not speed:
            speed = "normal"  # Default fallback
            self.logger.debug(f"Speed parameter not provided, using default: {speed}")
            
        # Validate speed parameter
        valid_speeds = ["very_slow", "slow", "normal", "fast", "very_fast"]
        if speed not in valid_speeds:
            # Default to normal for invalid speeds
            self.logger.warning(f"Invalid speed '{speed}', defaulting to 'normal'")
            speed = "normal"

        # Validate text length (prevent memory issues)
        max_text_length = 10000  # Reasonable limit for TTS
        if len(text) > max_text_length:
            self.logger.error(f"Text too long: {len(text)} characters (max: {max_text_length})")
            raise ValueError(f"Text too long. Maximum length is {max_text_length} characters")

        cache_key = f"stream:{hashlib.sha1((text + speed).encode('utf-8')).hexdigest()}"
        self.logger.debug(f"Streaming cache key: {cache_key}")

        if cache_key in self.cache:
            self.logger.info(f"Streaming cache hit for key: {cache_key}")
            audio_buffer: BytesIO = self.cache[cache_key]
            audio_buffer.seek(0)
        else:
            try:
                self.logger.debug(f"Streaming cache miss, generating new audio")
                audio_buffer = self.model.text_to_speech_streaming(text, speed)
                audio_buffer.seek(0)
                self.cache[cache_key] = audio_buffer
                self.logger.info(f"Streaming audio generated and cached with key: {cache_key}")
            except ValueError as e:
                # Re-raise validation errors from the model
                self.logger.error(f"Validation error in streaming TTS synthesis: {str(e)}")
                raise ValueError(str(e))
            except Exception as e:
                # Log and re-wrap unexpected errors
                self.logger.error(f"Streaming TTS synthesis failed: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to synthesize streaming audio: {str(e)}")

        chunk_size = 8192

        async def _gen():
            self.logger.debug(f"Starting audio streaming with chunk_size: {chunk_size}")
            bytes_sent = 0
            while True:
                chunk = audio_buffer.read(chunk_size)
                if not chunk:
                    break
                bytes_sent += len(chunk)
                yield chunk
            self.logger.info(f"Audio streaming completed, total bytes sent: {bytes_sent}")

        return _gen()
