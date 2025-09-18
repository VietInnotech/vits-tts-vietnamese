#!/usr/bin/env python3
"""
Text-to-Speech module using Piper TTS for Vietnamese.
Maintains the same API as the original tts.py for compatibility.
"""

import json
import time
from pathlib import Path
from typing import Optional
from io import BytesIO
import wave


from piper import PiperVoice, SynthesisConfig
from .config import get_tts_config
from .logging_config import logger

# Speed mapping - same as original
SPEED_VALUES = {
    "very_slow": 1.5,
    "slow": 1.2,
    "normal": 1.0,
    "fast": 0.6,
    "very_fast": 0.4,
}

SAMPLE_RATE = 22050
NOISE_SCALE = 0.5
NOISE_SCALE_W = 0.6


class PiperTTS:
    """Piper TTS wrapper that maintains compatibility with original TTS API."""

    def __init__(self, model_path: str):
        """Initialize Piper TTS with the given model."""
        self.model_path = model_path
        self.config_path = f"{model_path}.json"

        # Load the voice model
        logger.info(f"Loading Piper voice model: {model_path}")
        self.voice = PiperVoice.load(model_path)
        # Log attributes of the loaded voice to check for unexpected module references
        logger.debug(f"PiperVoice instance attributes: {[attr for attr in dir(self.voice) if not attr.startswith('_')]}")
        for attr_name in dir(self.voice):
            if not attr_name.startswith('_'):
                attr_value = getattr(self.voice, attr_name)
                if isinstance(attr_value, type):
                    logger.debug(f"PiperVoice.{attr_name} is a type: {attr_value}")
                elif hasattr(attr_value, "__module__") and "pdb" in str(attr_value.__module__):
                    logger.warning(
                        f"PiperVoice.{attr_name} potentially related to pdb: {attr_value} (module: {getattr(attr_value, '__module__', 'N/A')})"
                    )

        # Load configuration
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Load global TTS config (from configs/config.yaml) and set noise parameters with fallbacks.
        # Preference order: YAML tts.* > model config inference.* > hardcoded defaults.
        try:
            tts_cfg = get_tts_config()
        except Exception:
            tts_cfg = {}

        self.noise_scale = tts_cfg.get(
            "noise_scale",
            self.config.get("inference", {}).get("noise_scale", NOISE_SCALE),
        )
        self.noise_w = tts_cfg.get(
            "noise_w",
            self.config.get("inference", {}).get("noise_w", NOISE_SCALE_W),
        )

    def text_to_speech(
        self, text: str, speed: str = "normal", output_path: Optional[str] = None
    ) -> str:
        """
        Convert text to speech using Piper TTS.

        Args:
            text: Text to synthesize
            speed: Speech speed (very_slow, slow, normal, fast, very_fast)
            output_path: Optional output path. If None, generates a hash-based path

        Returns:
            Path to the generated audio file

        Raises:
            ValueError: If text is empty or speed is invalid
        """
        # Validate input text
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Validate speed
        if speed not in SPEED_VALUES:
            raise ValueError(
                f"Invalid speed '{speed}'. Must be one of: {', '.join(SPEED_VALUES.keys())}"
            )

        if output_path is None:
            # Generate hash-based output path like original
            import hashlib

            hash_of_text = hashlib.md5(f"{text}_{speed}".encode()).hexdigest()
            tts_cfg = get_tts_config()
            audio_output_dir = tts_cfg.get("audio_output_dir", "audio/")
            output_path = str(Path(audio_output_dir) / f"{hash_of_text}.wav")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Map speed to length_scale
        length_scale = SPEED_VALUES[speed]

        # Create synthesis config
        syn_config = SynthesisConfig(
            length_scale=length_scale,
            noise_scale=self.noise_scale,
            noise_w_scale=self.noise_w,
        )

        logger.info(f"Synthesizing with speed '{speed}' (length_scale={length_scale})")
        start_time = time.perf_counter()

        # Synthesize to WAV file
        with wave.open(output_path, "wb") as wav_file:
            self.voice.synthesize_wav(text, wav_file, syn_config=syn_config)

        end_time = time.perf_counter()
        infer_sec = end_time - start_time

        logger.info(f"Synthesis completed in {infer_sec:.3f} seconds")
        logger.info(f"Audio saved to: {output_path}")

        return output_path

    def text_to_speech_streaming(self, text: str, speed: str = "normal") -> BytesIO:
        """
        Stream text to speech using Piper TTS.

        Args:
            text: Text to synthesize
            speed: Speech speed (very_slow, slow, normal, fast, very_fast)

        Returns:
            BytesIO buffer containing the audio data

        Raises:
            ValueError: If text is empty or speed is invalid
        """
        # Validate input text
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Validate speed
        if speed not in SPEED_VALUES:
            raise ValueError(
                f"Invalid speed '{speed}'. Must be one of: {', '.join(SPEED_VALUES.keys())}"
            )

        # Map speed to length_scale
        length_scale = SPEED_VALUES[speed]

        # Create synthesis config
        syn_config = SynthesisConfig(
            length_scale=length_scale,
            noise_scale=self.noise_scale,
            noise_w_scale=self.noise_w,
        )

        logger.info(f"Streaming synthesis with speed '{speed}' (length_scale={length_scale})")
        start_time = time.perf_counter()

        # Use streaming synthesis
        audio_chunks = []
        sample_rate = None
        sample_width = None
        channels = None

        for chunk in self.voice.synthesize(text, syn_config=syn_config):
            if sample_rate is None:
                sample_rate = chunk.sample_rate
                sample_width = chunk.sample_width
                channels = chunk.sample_channels

            audio_chunks.append(chunk.audio_int16_bytes)

        # Ensure we have valid audio parameters
        if sample_rate is None or sample_width is None or channels is None:
            raise RuntimeError("No audio data generated")

        # Combine all chunks
        audio_data = b"".join(audio_chunks)

        # Create BytesIO buffer with WAV header
        audio_buffer = BytesIO()

        # Write WAV header and data
        with wave.open(audio_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)

        audio_buffer.seek(0)  # Reset buffer position

        end_time = time.perf_counter()
        infer_sec = end_time - start_time

        logger.info(f"Streaming synthesis completed in {infer_sec:.3f} seconds")

        return audio_buffer


# Maintain backward compatibility with original API
def text_to_speech(text: str, speed: str, model_name: str, hash_of_text: str) -> str:
    """Main entry point - maintains original API."""
    tts = PiperTTS(model_name)
    tts_cfg = get_tts_config()
    audio_output_dir = tts_cfg.get("audio_output_dir", "audio/")
    return tts.text_to_speech(text, speed, str(Path(audio_output_dir) / f"{hash_of_text}.wav"))


def text_to_speech_streaming(text: str, speed: str, model_name: str) -> BytesIO:
    """Streaming version - maintains original API."""
    tts = PiperTTS(model_name)
    return tts.text_to_speech_streaming(text, speed)


# Additional utility functions for the new Piper implementation
def create_piper_tts(model_path: str) -> PiperTTS:
    """Create a PiperTTS instance for repeated use."""
    return PiperTTS(model_path)


def get_available_voices() -> list:
    """Get list of available voice models."""
    # This would typically scan a voices directory or use a voice manager
    # For now, return our Vietnamese model
    return ["models/pretrained_vi.onnx"]


if __name__ == "__main__":
    # Test the new implementation
    logger.info("Testing Piper TTS implementation...")

    tts = PiperTTS("models/pretrained_vi.onnx")

    test_text = "Xin chào! Đây là thử nghiệm với Piper TTS."
    output_path = tts.text_to_speech(test_text, "normal")

    logger.info(f"Test completed. Audio saved to: {output_path}")

