# COMPONENT_PIPER_TTS Documentation

This document describes the Piper TTS component that has been integrated into the Vietnamese TTS project.

## Overview

The Piper TTS component provides a modern, efficient text-to-speech implementation that replaces the custom VITS architecture while maintaining full API compatibility. It is now integrated into the application through dependency injection via the `TTSService`.

## Architecture

The Piper TTS component consists of several key modules:

### Core Modules

1. **[`tts.py`](../src/vits_tts/tts.py)** - Main Piper TTS implementation

   - `PiperTTS` class: Core TTS engine wrapper
   - `text_to_speech()`: File-based synthesis function
   - `text_to_speech_streaming()`: Streaming synthesis function
   - `create_piper_tts()`: Factory function for creating PiperTTS instances

2. **[`core/tts_service.py`](../src/vits_tts/core/tts_service.py)** - Service layer that uses PiperTTS

   - `TTSService` class: Business logic layer that injects and uses PiperTTS
   - Handles caching and file system operations

3. **[`app.py`](../src/vits_tts/app.py)** - Application factory with dependency injection

   - `provide_piper_tts()`: Provider function for creating PiperTTS instances
   - `provide_tts_service()`: Provider function for creating TTSService with dependencies

4. **[`api/routers.py`](../src/vits_tts/api/routers.py)** - API controllers

   - `TTSController` class: Handles HTTP requests and uses TTSService

5. **[`api/schemas.py`](../src/vits_tts/api/schemas.py)** - Pydantic models

   - `TTSRequest` and `TTSResponse`: Request and response validation models

### Dependencies

- **piper-tts**: Core Piper TTS library (>=1.3.0, <2)
- **onnxruntime**: ONNX runtime for model inference (>=1.22.1, <2)
- **piper-phonemize**: Phonemization support (>=1.1.0, <2)
- **litestar**: Web framework (>=2.0.0)
- **pydantic**: Data validation (>=2.4.2)
- **cachetools**: Caching functionality (>=5.3.0, <6)

## Key Classes and Functions

### PiperTTS Class

```python
class PiperTTS:
    def __init__(self, model_path: str):
        """Initialize Piper TTS with voice model."""

    def text_to_speech(self, text: str, speed: str = "normal", output_path: Optional[str] = None) -> str:
        """Convert text to speech and save to file."""

    def text_to_speech_streaming(self, text: str, speed: str = "normal") -> BytesIO:
        """Convert text to speech and return as memory buffer."""
```

### TTSService Class

```python
class TTSService:
    def __init__(self, cache: LRUCache, config: dict, model: PiperTTS):
        """Initialize TTS service with dependencies."""
        self.cache = cache
        self.config = config
        self.model = model  # Injected PiperTTS instance

    async def handle_tts_request(self, text: str, speed: str) -> dict:
        """Handle file-based TTS request."""

    async def handle_tts_streaming_request(self, text: str, speed: str) -> AsyncGenerator[bytes, None]:
        """Handle streaming TTS requests."""
```

### Dependency Injection

The `PiperTTS` class is now injected into the `TTSService` through LiteStar's dependency injection system:

```python
# In app.py
def provide_piper_tts() -> PiperTTS:
    """Provider: create a shared PiperTTS instance based on config."""
    tts_cfg = get_config().get("tts", {}) or {}
    model_path = tts_cfg.get("model_path", "models/pretrained_vi.onnx")
    return create_piper_tts(model_path)

def provide_tts_service() -> TTSService:
    """Provider: construct TTSService with its dependencies."""
    cache = provide_audio_cache()
    config = get_config()
    model = provide_piper_tts()
    return TTSService(cache=cache, config=config, model=model)
```

## Performance Improvements

The migration to LiteStar with Piper TTS provides significant performance improvements:

- **Synthesis Speed**: 3-5x faster (0.1-0.3s vs 1.0-1.2s)
- **Memory Usage**: More efficient memory management with dependency injection
- **Streaming**: Better real-time streaming capabilities
- **Scalability**: Improved architecture for handling concurrent requests

## Configuration

### Speed Settings

The component supports the same speed settings as the original implementation:

- `very_slow`: 1.5x length scale
- `slow`: 1.2x length scale
- `normal`: 1.0x length scale (default)
- `fast`: 0.6x length scale
- `very_fast`: 0.4x length scale

### Audio Parameters

- **Sample Rate**: 22050 Hz
- **Channels**: Mono (1 channel)
- **Sample Width**: 16-bit (2 bytes)
- **Format**: WAV

### Voice Smoothness Parameters

The component supports configurable voice smoothness parameters:

- **`noise_scale`**: Controls randomness in generated audio (configurable in `configs/config.yaml`)
- **`noise_w`**: Affects posterior variance of acoustic model (configurable in `configs/config.yaml`)
- **`length_scale`**: Adjusts speaking rate (mapped from speed settings)

### Noise Parameter Priority

The noise parameters (`noise_scale` and `noise_w`) follow a specific priority order when determining their final values:

1. **YAML Configuration**: Values from [`configs/config.yaml`](configs/config.yaml) (`tts.noise_scale` and `tts.noise_w`)
2. **JSON Configuration**: Values from the model's `.onnx.json` file (`inference.noise_scale` and `inference.noise_w`)
3. **Hardcoded Defaults**: Fallback values defined in [`src/vits_tts/tts.py`](src/vits_tts/tts.py:31-32) (NOISE_SCALE = 0.5, NOISE_SCALE_W = 0.6)

This priority order ensures that YAML configuration takes precedence over model JSON configuration, which in turn takes precedence over hardcoded defaults. This allows for easy tuning of voice smoothness through configuration changes without modifying the code or model files.

## Usage Examples

### Basic Usage

```python
from src.vits_tts.tts import PiperTTS

# Initialize TTS
tts = PiperTTS("models/v2/finetuning_pretrained_vi.onnx")

# Synthesize text
audio_path = tts.text_to_speech("Xin chào thế giới!", "normal")
print(f"Audio saved to: {audio_path}")

# Stream synthesis
audio_buffer = tts.text_to_speech_streaming("Xin chào!", "fast")
```

### Through Dependency Injection

```python
# The TTSService is automatically injected with a PiperTTS instance
# when using the LiteStar application

from src.vits_tts.core.tts_service import TTSService

# In a service or controller
async def process_tts_request(service: TTSService, text: str, speed: str):
    result = await service.handle_tts_request(text, speed)
    return result
```

### API Usage

```bash
# File-based synthesis
curl "http://localhost:8888/tts?text=Xin chào!&speed=normal"

# Streaming synthesis
curl "http://localhost:8888/tts/stream?text=Xin chào!&speed=fast" --output audio.wav
```

## Testing

The component includes comprehensive tests:

1. **Basic Functionality**: Tests in `tests/` directory
2. **API Endpoints**: [`test_migration_validation.py`](../tests/test_migration_validation.py)
3. **Migration Validation**: Ensures compatibility with new LiteStar architecture
4. **Performance Comparison**: Validates improvements over original implementation

## Error Handling

The component includes robust error handling for:

- Invalid voice models
- Unsupported text content
- File system errors
- Memory allocation issues
- Configuration errors

## Future Enhancements

Potential areas for future development:

1. **Custom Dictionary Support**: Integration with Vietnamese custom dictionaries
2. **Voice Model Management**: Dynamic loading of multiple voice models
3. **GPU Acceleration**: CUDA support for faster synthesis
4. **Real-time Streaming**: Enhanced streaming for live applications
5. **Advanced Caching**: More sophisticated caching strategies

## Technical Debt

### Unused Modules

The following modules exist in the codebase but are currently not used in the LiteStar-based implementation:

- **[`src/vits_tts/utils.py`](src/vits_tts/utils.py)**: Contains audio processing utilities (WAV file reading/writing, sample rate conversion, normalization) that were part of the original VITS implementation but are not utilized by the current Piper TTS architecture.

- **[`src/vits_tts/validate.py`](src/vits_tts/validate.py)**: Contains Tornado-specific validation decorators that are not compatible with the current LiteStar implementation using Pydantic models for request validation.

- **[`src/vits_tts/debug_logger.py`](src/vits_tts/debug_logger.py)**: A custom debug logging implementation that has been superseded by the structured logging system using `loguru` configured in [`src/vits_tts/logging_config.py`](src/vits_tts/logging_config.py).

These modules represent technical debt that should be addressed in future refactoring efforts to improve code maintainability and reduce the codebase size.

## Migration Notes

- The migration maintains full backward compatibility
- Original implementation remains available via configuration
- Performance improvements are immediately available
- No changes required to existing client code
- `PiperTTS` is now injected into `TTSService` through dependency injection
- The application uses LiteStar instead of Tornado for better async support
