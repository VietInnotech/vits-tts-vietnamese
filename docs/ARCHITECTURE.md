# Architecture

This document outlines the architecture of the Vietnamese TTS project, including recent production-readiness improvements and the migration from Tornado to LiteStar, with a focus on API-only functionality.

## Current Architecture (LiteStar with Piper TTS)

The architecture has been successfully migrated to use the Piper TTS engine with the LiteStar API framework, featuring dependency injection, Pydantic models for request/response validation, and a modular component structure.

```mermaid
graph TD
    A[HTTP Request] --> B{LiteStar Application};
    B --> C[TTSController];
    C --> D{TTSService};
    D --> E{Piper TTS Engine};
    E --> F{Phonemization (espeak-ng)};
    F --> G{VITS Model (ONNX)};
    G --> H[Audio Output];

    I[config.yaml] --> J[Configuration Module<br/>config.py];
    J --> B;
    J --> D;
    J --> H[Server Port<br/>Model Paths];

    K[loguru] --> L[Logging Module<br/>logging_config.py];
    L --> M[Structured JSON Logs<br/>File & Console Output];

    N[cachetools] --> O[In-Memory Cache<br/>LRU Strategy];
    O --> P[Audio Data Storage<br/>Cache Hit/Miss];
    P --> D;
    P -> Q[Audio File Output];

    R[Pydantic] --> S[API Schemas<br/>api/schemas.py];
    S --> C;
```

## LiteStar-Based Architecture

The project has been refactored to use the LiteStar API framework, providing a modern, async-first Python API service with robust dependency injection and OpenAPI documentation capabilities.

### Core Components

1. **[`LiteStar Application`](src/vits_tts/app.py:63)**: Main application instance configured with routes, dependencies, and static files.
2. **[`TTSController`](src/vits_tts/api/routers.py:8)**: Handles HTTP requests for TTS endpoints.
3. **[`TTSService`](src/vits_tts/core/tts_service.py:11)**: Business logic layer for TTS processing.
4. **[`PiperTTS`](src/vits_tts/tts.py:35)**: Core TTS engine wrapper for Piper model.
5. **[`RootController`](src/vits_tts/api/routers.py:57)**: Handles root endpoint redirection to Swagger UI.

### Project Structure

The project is organized into three main components:

```
src/vits_tts/
├── api/              # API layer
│   ├── routers.py   # Route handlers and controllers
│   └── schemas.py   # Pydantic models for request/response validation
├── core/             # Core business logic
│   ├── caching.py   # Caching utilities
│   └── tts_service.py # TTS service implementation
├── app.py            # LiteStar application factory
├── main.py           # Application entry point
├── config.py         # Configuration management
├── tts.py            # Piper TTS implementation
├── utils.py          # Audio processing utilities (unused)
├── validate.py       # Tornado validation decorators (unused)
└── ...
```

### API Documentation

The application now includes auto-generated OpenAPI documentation powered by Litestar's built-in support. This provides a comprehensive view of the API endpoints, request/response schemas, and allows for interactive testing of the API.

- **Swagger UI**: Accessible at `/docs` for interactive API exploration.
- **OpenAPI Schema**: Available at `/schema/openapi.json` in JSON format.
- **Root Redirect**: The root endpoint `/` redirects to the Swagger UI documentation.

### Dependency Injection

LiteStar's dependency injection system manages service lifecycles and dependencies:

- **[`provide_piper_tts()`](src/vits_tts/app.py:44)**: Creates and configures the Piper TTS instance.
- **[`provide_tts_service()`](src/vits_tts/app.py:51)**: Constructs the TTSService with its dependencies (cache, config, model).
- **[`provide_audio_cache()`](src/vits_tts/core/caching.py)**: Provides the LRU cache instance.

### Request/Response Validation

Pydantic models in [`api/schemas.py`](src/vits_tts/api/schemas.py) ensure data validation:

- **[`TTSRequest`](src/vits_tts/api/schemas.py:5)**: Validates incoming TTS requests.
- **[`TTSResponse`](src/vits_tts/api/schemas.py:12)**: Defines the structure of TTS responses.

## Production-Ready Components

### 1. Configuration System

The application uses a YAML-based configuration system that externalizes all configuration from the codebase.

#### Components

- **[`configs/config.yaml`](configs/config.yaml)**: Main configuration file containing all settings
- **[`config.py`](src/vits_tts/config.py)**: Configuration loader and accessor module

#### Features

- **Externalized Configuration**: All settings are stored in [`configs/config.yaml`](configs/config.yaml) rather than hardcoded
- **Environment-Specific Settings**: Easy to switch between development, staging, and production configurations
- **Validation**: Built-in validation and fallback to default values
- **Type Safety**: Structured access to configuration sections

#### Configuration Sections

```yaml
server:
  port: 8888 # Server port
  host: "0.0.0.0" # Host to bind to

tts:
  model_path: "models/v2/finetuning_pretrained_vi.onnx" # ONNX model path
  config_path: "models/v2/finetuning_pretrained_vi.onnx.json" # Model config path
  audio_output_dir: "audio/" # Audio output directory
  noise_scale: 0.4 # Audio generation noise scale
  noise_w: 0.5 # Audio generation noise weight

logging:
  level: "INFO" # Logging level
```

### 2. Structured Logging System

The application implements structured logging using `loguru` for improved observability and debugging.

#### Components

- **[`logging_config.py`](src/vits_tts/logging_config.py)**: Logger configuration module
- **[`configs/config.yaml`](configs/config.yaml)**: Logging configuration section

#### Features

- **JSON Format**: Logs are output in JSON format for easy parsing and analysis
- **Multiple Outputs**: Logs to both console and file (`logs/tts_server.log`)
- **Configurable Levels**: Log levels can be adjusted via configuration
- **File Rotation**: Automatic log rotation (10MB per file) with 7-day retention
- **Error Diagnostics**: Includes stack traces and diagnostic information

#### Log Format

```json
{
  "time": "2025-01-17T04:46:46.446Z",
  "level": "INFO",
  "name": "server",
  "function": "handle_request",
  "line": 123,
  "message": "Processing TTS request for text: Xin chào bạn"
}
```

### 3. In-Memory Caching Layer

The application uses `cachetools` to implement an in-memory LRU (Least Recently Used) cache for improved performance.

#### Components

- **[`caching.py`](src/vits_tts/core/caching.py)**: Cache implementation module
- **Cache Integration**: Integrated into TTS processing pipeline via [`TTSService`](src/vits_tts/core/tts_service.py:11)

#### Features

- **Reduced I/O**: Minimizes disk access for repeated requests
- **Improved Response Times**: Faster synthesis for cached content
- **Memory Efficient**: LRU strategy ensures optimal memory usage
- **Cache Hit/Miss Tracking**: Provides visibility into cache effectiveness

#### Caching Strategy

- **Cache Key**: Generated from text content and speed parameters
- **Cache Size**: Configurable LRU cache size
- **Cache Persistence**: In-memory only (application restart clears cache)
- **Audio Serving**: Both `/tts` and `/tts/stream` endpoints utilize the in-memory cache for optimal performance

### 4. Standardized Dependency Management

The project uses `pixi` for dependency management to ensure reproducible builds and consistent environments.

#### Components

- **[`pixi.toml`](pixi.toml)**: Main dependency specification file
- **Development Dependencies**: Includes linting and formatting tools
- **Task Management**: Predefined tasks for development, testing, and deployment

#### Features

- **Locked Dependencies**: Ensures reproducible builds across environments
- **Cross-Platform**: Works consistently across different operating systems
- **Development Tools**: Integrated `ruff` and `black` for code quality
- **Environment Management**: Isolated Python environments
- **Task Automation**: Predefined tasks like `pixi run server`, `pixi run test`, `pixi run lint`

#### Deployment Configuration

The `pixi.toml` includes deployment-specific configurations:

```toml
[workspace]
authors = ["lkless <leakless21@gmail.com>"]
channels = ["conda-forge"]
name = "vits-tts-vietnamese"
platforms = ["linux-64","win-64"]
version = "0.1.0"

[tasks]
server = "PYTHONPATH=src python -m vits_tts.main --no-ui"
test = "PYTHONPATH=$PYTHONPATH:$(pwd)/src pytest"
lint = "ruff check . && black --check ."

[dependencies]
python = "<3.13"
loguru = ">=0.7.3,<0.8"

[pypi-dependencies]
litestar = ">=2.0.0"
uvicorn = ">=0.23.2"
piper-tts = ">=1.3.0, <2"
# ... other dependencies
```

## Migration from Tornado to LiteStar

The migration from Tornado to LiteStar has been completed with the following key improvements:

### Key Changes

- **Framework Change**: Replaced Tornado with LiteStar for better async support and modern features
- **Dependency Injection**: Implemented LiteStar's dependency injection system for better service management
- **Request Validation**: Added Pydantic models for robust request/response validation
- **Project Structure**: Refactored into `api`, `core`, and `app` components for better separation of concerns
- **Testing**: Updated testing approach with LiteStar's test client

### Migration Benefits

- **Performance**: Better async support for improved throughput
- **Maintainability**: Cleaner code structure with dependency injection
- **Developer Experience**: Enhanced tooling and type safety
- **Scalability**: More robust architecture for future enhancements
- **Documentation**: Built-in OpenAPI support

### Backward Compatibility

The API endpoints remain the same to ensure compatibility with existing clients:

- `/tts`: File-based TTS synthesis
- `/tts/stream`: Streaming TTS synthesis

## Audio Serving Mechanism

The API-only architecture provides two primary endpoints for audio synthesis, both optimized for performance and reliability:

### `/tts` Endpoint

- **Function**: Generates audio files and returns them as downloadable content
- **Output Format**: WAV audio files with standard Vietnamese TTS processing
- **Caching**: Utilizes LRU cache for repeated requests to minimize processing time
- **File Management**: Audio files are stored in the configured output directory with unique filenames

### `/tts/stream` Endpoint

- **Function**: Provides streaming audio synthesis for real-time applications
- **Output Format**: Direct audio streaming without intermediate file storage
- **Performance**: Optimized for low-latency responses with in-memory caching
- **Use Cases**: Ideal for applications requiring immediate audio playback

### Audio Processing Pipeline

Both endpoints follow the same optimized processing pipeline:

1. **Request Validation**: Pydantic models validate input parameters
2. **Cache Check**: LRU cache is queried for existing audio content
3. **TTS Processing**: Piper TTS engine generates audio from text
4. **Audio Enhancement**: Noise parameters applied for voice smoothness
5. **Response Generation**: Audio returned in appropriate format (file download or stream)

## Component Responsibilities

| Component         | Responsibility                          | Dependencies                     | Interface                        |
| ----------------- | --------------------------------------- | -------------------------------- | -------------------------------- |
| **LiteStar App**  | Application lifecycle and configuration | `litestar`, `uvicorn`            | HTTP server interface            |
| **TTSController** | HTTP request handling and routing       | `TTSController`, `TTSService`    | RESTful API endpoints            |
| **TTSService**    | Business logic for TTS processing       | `PiperTTS`, `LRUCache`, `config` | Service methods                  |
| **PiperTTS**      | Core TTS synthesis functionality        | `piper-tts`, `onnxruntime`       | Text → Audio conversion          |
| **Configuration** | Application settings management         | `pyyaml`                         | Config access for all components |
| **Logging**       | Structured logging system               | `loguru`                         | Logging for all components       |
| **Caching**       | In-memory audio data caching            | `cachetools`                     | Cache interface for TTSService   |

## Storage Considerations

- **Model Storage**: ONNX models stored in `models/v2/` directory
- **Audio Storage**: Generated audio files stored in `audio/` directory
- **Log Storage**: Application logs stored in `data/logs/` directory with rotation
- **Cache Storage**: In-memory only, no persistent storage

## Compute Requirements

- **CPU**: Multi-core CPU recommended for optimal performance
- **Memory**: Sufficient memory for ONNX model loading and in-memory cache
- **Storage**: SSD storage recommended for faster model loading and audio I/O

## Interface Specifications

### External Interfaces

- **HTTP API**: RESTful interface at `/tts` and `/tts/stream` endpoints
- **Configuration File**: YAML-based configuration via [`configs/config.yaml`](configs/config.yaml)
- **Log Output**: JSON-formatted logs to console and file

### Internal Interfaces

- **Configuration Module**: Provides typed access to settings
- **Logging Module**: Provides structured logging capabilities
- **Cache Module**: Provides in-memory storage for audio data
- **TTS Engine**: Provides text-to-speech synthesis capabilities

## Voice Smoothness Tuning

### Key Parameters

The Piper TTS model provides several key parameters that can be tuned to achieve smoother voice output. These parameters control various aspects of the audio generation process, including randomness, acoustic modeling, and speaking rate.

#### `noise_scale`

- **Description**: Controls the randomness in the generated audio. Lowering this value reduces the variability in the output, leading to a smoother, more consistent voice.
- **Default Value**: 0.667
- **Recommended Range for Smoothness**: 0.4-0.6
- **Trade-off**: Lower values improve smoothness but may reduce expressiveness and natural variation in the voice.

#### `noise_w`

- **Description**: Affects the posterior variance of the acoustic model. Reducing this value can help stabilize the audio output and contribute to a smoother result.
- **Default Value**: 0.8
- **Recommended Range for Smoothness**: 0.5-0.7
- **Trade-off**: Lower values can improve smoothness but may make the voice sound less dynamic or robotic if set too low.

#### `length_scale`

- **Description**: Adjusts the speaking rate by scaling the length of phonemes. A higher value slows down the speech, which can improve clarity and smoothness by reducing the pace at which audio is generated.
- **Default Value**: 1.0
- **Recommended Range for Smoothness**: 1.2 (slower speech)
- **Trade-off**: Higher values improve clarity and smoothness but may make the speech unnaturally slow.

### Parameter Locations

These parameters are configured in two locations within the project:

1. **Model Configuration Files**: The parameters are defined in the `.onnx.json` configuration files associated with each model. For example:

   - [`models/v2/finetuning_pretrained_vi.onnx.json`](models/v2/finetuning_pretrained_vi.onnx.json)

2. **Source Code Implementation**: The parameters are also hardcoded as global constants in the TTS module:
   - [`src/vits_tts/tts.py`](src/vits_tts/tts.py:31-32)

### Configuration Priority

The `noise_scale` and `noise_w` parameters are now configurable in [`configs/config.yaml`](configs/config.yaml) and these values override the defaults set in the model's JSON configuration and the hardcoded values in [`src/vits_tts/tts.py`](src/vits_tts/tts.py). The configuration loading logic in [`src/vits_tts/tts.py`](src/vits_tts/tts.py:69-76) follows this priority order:

1. **YAML Configuration**: Values from `configs/config.yaml` (tts.noise_scale and tts.noise_w)
2. **Model Configuration**: Values from the `.onnx.json` file (inference.noise_scale and inference.noise_w)
3. **Hardcoded Defaults**: Fallback values defined in [`src/vits_tts/tts.py`](src/vits_tts/tts.py:31-32) (NOISE_SCALE = 0.5, NOISE_SCALE_W = 0.6)

This allows for easy tuning of voice smoothness through configuration changes without modifying the code or model files.
When modifying these parameters, changes in the source code will take precedence during model inference, while the `.onnx.json` files typically serve as the reference configuration for the model itself.

## Changelog

### 2025-09-18 - Web Interface Removal

- **Removed**: Web interface components and static file serving
- **Updated**: Architecture refactored to API-only service
- **Improved**: Audio serving mechanism documented and optimized
- **Changed**: Configuration simplified by removing CORS and web-specific settings
- **Enhanced**: Both `/tts` and `/tts/stream` endpoints now utilize in-memory caching for optimal performance
