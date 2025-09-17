# Architecture

This document outlines the architecture of the Vietnamese TTS project, including recent production-readiness improvements.

## Current Architecture (Migrated to Piper)

The architecture has been successfully migrated to use the Piper TTS engine with enhanced production features including standardized dependency management, externalized configuration, structured logging, and in-memory caching.

```mermaid
graph TD
    A[Input Text] --> B{Piper TTS Engine};
    B --> C{Phonemization (espeak-ng)};
    C --> D{VITS Model (ONNX)};
    D --> E[Audio Output];

    F[config.yaml] --> G[Configuration Module<br/>config.py];
    G --> B;
    G --> H[Server Port<br/>CORS Origins<br/>Model Paths];

    I[loguru] --> J[Logging Module<br/>logging_config.py];
    J --> K[Structured JSON Logs<br/>File & Console Output];

    L[cachetools] --> M[In-Memory Cache<br/>LRU Strategy];
    M --> N[Audio Data Storage<br/>Cache Hit/Miss];
    N --> D;
    N --> O[Audio File Output];
```

## Production-Ready Components

### 1. Configuration System

The application now uses a YAML-based configuration system that externalizes all configuration from the codebase.

#### Components

- **[`config.yaml`](../config.yaml)**: Main configuration file containing all settings
- **[`config.py`](../config.py)**: Configuration loader and accessor module

#### Features

- **Externalized Configuration**: All settings are stored in [`config.yaml`](../config.yaml) rather than hardcoded
- **Environment-Specific Settings**: Easy to switch between development, staging, and production configurations
- **Validation**: Built-in validation and fallback to default values
- **Type Safety**: Structured access to configuration sections

#### Configuration Sections

```yaml
server:
  port: 8888 # Server port
  cors_origins: # CORS policy origins
    - "http://localhost:3000"
    - "http://127.0.0.1:3000"

tts:
  model_path: "fine-tuning-model/v2/finetuning_pretrained_vi.onnx" # ONNX model path
  config_path: "fine-tuning-model/v2/finetuning_pretrained_vi.onnx.json" # Model config path
  audio_output_dir: "audio/" # Audio output directory

logging:
  level: "INFO" # Logging level
```

### 2. Structured Logging System

The application implements structured logging using `loguru` for improved observability and debugging.

#### Components

- **[`logging_config.py`](../logging_config.py)**: Logger configuration module
- **[`config.yaml`](../config.yaml)**: Logging configuration section

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

- **[`cachetools`](../pixi.toml:26)**: Dependency for caching functionality
- **Cache Implementation**: Integrated into TTS processing pipeline

#### Features

- **Reduced I/O**: Minimizes disk access for repeated requests
- **Improved Response Times**: Faster synthesis for cached content
- **Memory Efficient**: LRU strategy ensures optimal memory usage
- **Cache Hit/Miss Tracking**: Provides visibility into cache effectiveness

#### Caching Strategy

- **Cache Key**: Generated from text content and speed parameters
- **Cache Size**: Configurable LRU cache size
- **Cache Persistence**: In-memory only (application restart clears cache)
- **File Output**: Original `/tts` endpoint saves to disk, `/tts/stream` uses memory cache directly

### 4. Standardized Dependency Management

The project uses `pixi` for dependency management to ensure reproducible builds and consistent environments.

#### Components

- **[`pixi.toml`](../pixi.toml)**: Main dependency specification file
- **Development Dependencies**: Includes linting and formatting tools

#### Features

- **Locked Dependencies**: Ensures reproducible builds across environments
- **Cross-Platform**: Works consistently across different operating systems
- **Development Tools**: Integrated `ruff` and `black` for code quality
- **Environment Management**: Isolated Python environments

## Migration Overview

The migration from the custom VITS implementation to Piper TTS has been completed with the following key improvements:

### Key Changes

- **Simplified Architecture**: Replaced custom VITS implementation with `piper-tts` library
- **Improved Performance**: Faster synthesis times (0.1-0.3s vs 1.0-1.2s)
- **Streamlined Dependencies**: Maintained ONNX runtime compatibility
- **Backward Compatibility**: Original API preserved for seamless transition
- **Production Hardening**: Added configuration management, logging, and caching

### Components

1. **Piper TTS Engine**: Core synthesis engine that handles phonemization and audio generation
2. **espeak-ng Integration**: Enhanced phonemization with Vietnamese language support
3. **ONNX Runtime**: Continued use of existing Vietnamese voice models
4. **API Compatibility Layer**: Maintains original function signatures
5. **Configuration Management**: Externalized configuration via YAML
6. **Structured Logging**: JSON-formatted logs for observability
7. **In-Memory Caching**: Performance optimization using `cachetools`

### Migration Benefits

- **Performance**: 3-5x faster synthesis times
- **Reliability**: More stable and well-tested codebase
- **Maintainability**: Simplified code structure
- **Extensibility**: Easier to add new features and voices
- **Observability**: Structured logging for better debugging and monitoring
- **Flexibility**: Externalized configuration for different environments
- **Scalability**: In-memory caching for improved response times

### Backward Compatibility

The migration maintains full backward compatibility through the [`tts_migrated.py`](../tts_migrated.py) module, allowing seamless switching between implementations if needed.

## Component Responsibilities

| Component                | Responsibility                       | Dependencies                                  | Interface                           |
| ------------------------ | ------------------------------------ | --------------------------------------------- | ----------------------------------- |
| **Piper TTS Engine**     | Audio synthesis from text            | `piper-tts`, `onnxruntime`, `piper-phonemize` | Text input → Audio output           |
| **Configuration System** | Load and manage application settings | `pyyaml`                                      | Provides settings to all components |
| **Logging System**       | Generate and manage application logs | `loguru`                                      | Logs events from all components     |
| **Caching Layer**        | Store and retrieve audio data        | `cachetools`                                  | Cache hits reduce processing time   |
| **Web Server**           | Handle HTTP requests and responses   | `tornado`                                     | HTTP interface for TTS services     |
| **Model Loader**         | Load and manage ONNX models          | `onnxruntime`                                 | Provides model access to TTS engine |

## Storage Considerations

- **Model Storage**: ONNX models stored in `fine-tuning-model/` directory
- **Audio Storage**: Generated audio files stored in `audio/` directory
- **Log Storage**: Application logs stored in `logs/` directory with rotation
- **Cache Storage**: In-memory only, no persistent storage

## Compute Requirements

- **CPU**: Multi-core CPU recommended for optimal performance
- **Memory**: Sufficient memory for ONNX model loading and in-memory cache
- **Storage**: SSD storage recommended for faster model loading and audio I/O

## Interface Specifications

### External Interfaces

- **HTTP API**: RESTful interface at `/tts` and `/tts/stream` endpoints
- **Configuration File**: YAML-based configuration via [`config.yaml`](../config.yaml)
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

   - [`models/fine-tuning-model/v2/finetuning_pretrained_vi.onnx.json`](models/fine-tuning-model/v2/finetuning_pretrained_vi.onnx.json)

2. **Source Code Implementation**: The parameters are also hardcoded as global constants in the TTS module:
   - [`src/vits_tts/tts.py`](src/vits_tts/tts.py)

### Configuration Priority

The `noise_scale` and `noise_w` parameters are now configurable in [`configs/config.yaml`](configs/config.yaml) and these values override the defaults set in the model's JSON configuration and the hardcoded values in [`src/vits_tts/tts.py`](src/vits_tts/tts.py). The configuration loading logic in [`src/vits_tts/tts.py`](src/vits_tts/tts.py:47-61) follows this priority order:

1. **YAML Configuration**: Values from `configs/config.yaml` (tts.noise_scale and tts.noise_w)
2. **Model Configuration**: Values from the `.onnx.json` file (inference.noise_scale and inference.noise_w)
3. **Hardcoded Defaults**: Fallback values defined in [`src/vits_tts/tts.py`](src/vits_tts/tts.py:27-28) (NOISE_SCALE = 0.5, NOISE_SCALE_W = 0.6)

This allows for easy tuning of voice smoothness through configuration changes without modifying the code or model files.
When modifying these parameters, changes in the source code will take precedence during model inference, while the `.onnx.json` files typically serve as the reference configuration for the model itself.
