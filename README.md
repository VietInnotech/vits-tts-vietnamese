# Finetuining VITS Text-to-Speech Model in Vietnamese

We use Piper library to finetuning VITS for TTS tasks with different voice in Vietnamese.

We also built a LiteStar server to deploy TTS model on microservice with Docker.
The server uses ONNX model type to infer lightweight and excellent performance.

Video demo: <https://youtu.be/1mAhaP26aQE>

Read Project Docs: [Paper](https://github.com/phatjkk/vits-tts-vietnamese/blob/main/TTS_VITS_Docs_NguyenThanhPhat.pdf)

# How to run this project?

## Prerequisites

- [pixi](https://pixi.sh/) - A fast, cross-platform package manager for Python
- Docker (optional, for containerized deployment)

## Installation with pixi (Recommended)

The project now uses [`pixi.toml`](pixi.toml) for standardized dependency management. This ensures reproducible environments and consistent builds across development and production.

1. Install pixi by following the instructions at <https://pixi.sh/>

2. Install project dependencies:

   ```bash
   pixi install
   ```

3. Activate the pixi environment:

   ```bash
   pixi shell
   ```

## Configuration

The application uses a [`configs/config.yaml`](configs/config.yaml) file for configuration. This allows you to customize various aspects of the application without modifying the code.

### Configuration File (`configs/config.yaml`)

The configuration file is located at [`configs/config.yaml`](configs/config.yaml) and contains the following sections:

#### Server Configuration

```yaml
server:
  port: 8888 # Port for the TTS server
  host: "0.0.0.0" # Host to bind to
```

#### TTS Configuration

```yaml
ts:
  model_path: "fine-tuning-model/v2/finetuning_pretrained_vi.onnx" # Path to the ONNX model
  config_path: "fine-tuning-model/v2/finetuning_pretrained_vi.onnx.json" # Path to model config
  audio_output_dir: "audio/" # Directory for saving generated audio files
  noise_scale: 0.5 # Audio generation noise scale
  noise_w: 0.6 # Audio generation noise weight
```

#### Logging Configuration

```yaml
logging:
  level: "INFO" # Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Modifying Configuration

To modify the configuration:

1. Edit the [`configs/config.yaml`](configs/config.yaml) file directly
2. The application will automatically pick up changes on restart

### Environment Variables (Docker)

When running with Docker, you can override configuration values using environment variables:

| Variable               | Description                   | Default Value                                  | Example                                         |
| ---------------------- | ----------------------------- | ---------------------------------------------- | ----------------------------------------------- |
| `TTS_MODEL_PATH`       | Path to the ONNX model file   | `models/v2/finetuning_pretrained_vi.onnx`      | `models/infore/vi_VN-vais1000-medium.onnx`      |
| `TTS_CONFIG_PATH`      | Path to the model config JSON | `models/v2/finetuning_pretrained_vi.onnx.json` | `models/infore/vi_VN-vais1000-medium.onnx.json` |
| `TTS_AUDIO_OUTPUT_DIR` | Directory for audio output    | `audio/`                                       | `output/`                                       |
| `TTS_CACHE_SIZE`       | Cache size for TTS responses  | `100`                                          | `200`                                           |
| `TTS_DEFAULT_SPEED`    | Default speech speed          | `normal`                                       | `fast`                                          |
| `TTS_NOISE_SCALE`      | Noise scale parameter         | `0.4`                                          | `0.5`                                           |
| `TTS_NOISE_W`          | Noise W parameter             | `0.5`                                          | `0.6`                                           |
| `SERVER_PORT`          | Server port                   | `8888`                                         | `9000`                                          |
| `LOG_LEVEL`            | Logging level                 | `INFO`                                         | `DEBUG`                                         |

See [DOCKER.md](docs/DOCKER.md) for detailed instructions on using environment variables with Docker.

## Usage

### Running the Server

With the pixi environment activated:

```bash
pixi run server
```

Alternatively, you can use the provided [`start.sh`](start.sh) script:

```bash
./start.sh
```

Or, if you prefer to run directly:

```bash
PYTHONPATH=src python -m vits_tts.main
```

The server will start on port 8888 by default (as specified in [`configs/config.yaml`](configs/config.yaml:2)).

### With Docker (**_highly recommend_**)

This project includes Docker support for easy deployment. Both Vietnamese TTS models are now bundled in the Docker image:

1. **InfoRE Model**: `models/infore/vi_VN-vais1000-medium.onnx` (~63.2 MB)
2. **Fine-tuned V2 Model**: `models/v2/finetuning_pretrained_vi.onnx` (~63.1 MB) - **Default**

#### Quick Start with Docker

```bash
# Build and run with default settings (V2 model)
docker build -t vits-tts-vietnamese .
docker run -d -p 8888:8888 vits-tts-vietnamese
```

#### Using Docker Compose (Recommended for Development)

For development with live reloading and volume mounts:

```bash
docker-compose up --build
```

This will start the service on port 8888 (<http://localhost:8888>) with volume mounts for:

- Source code (`./src` → `/app/src`)
- Configuration (`./configs` → `/app/configs`)
- Audio output (`./audio` → `/app/audio`)
- Logs (`./logs` → `/app/logs`)

**Note**: Models are now bundled in the image, so no external model volume mount is needed.

#### Using Docker Directly

To build and run with Docker directly:

```bash
# Build the image
docker build -t vits-tts-vietnamese .

# Run with default settings (V2 model)
docker run -d -p 8888:8888 vits-tts-vietnamese
```

#### Custom Port Mapping

To run on a different port (e.g., 5004):

```bash
docker run -d -p 5004:8888 vits-tts-vietnamese
```

Then access the API at `http://localhost:5004/tts?text=Xin chào bạn&speed=normal`

For detailed Docker usage instructions, see [DOCKER.md](docs/DOCKER.md).

### Model Selection

#### Default Model (Fine-tuned V2)

The V2 model is used by default - no configuration needed:

```bash
docker run -d -p 8888:8888 vits-tts-vietnamese
```

#### Using InfoRE Model

Switch to the InfoRE model using environment variables:

```bash
docker run -d \
  -e TTS_MODEL_PATH=models/infore/vi_VN-vais1000-medium.onnx \
  -e TTS_CONFIG_PATH=models/infore/vi_VN-vais1000-medium.onnx.json \
  -p 8888:8888 \
  vits-tts-vietnamese
```

#### Using Custom Models

To use your own model files:

```bash
docker run -d \
  -v /path/to/your/models:/app/custom_models \
  -e TTS_MODEL_PATH=custom_models/your_model.onnx \
  -e TTS_CONFIG_PATH=custom_models/your_model.json \
  -p 8888:8888 \
  vits-tts-vietnamese
```

### Health Check Endpoint

The Docker container includes a health check endpoint:

```
GET http://localhost:{port}/health
```

Returns:

```json
{
  "status": "healthy",
  "message": "TTS service is running"
}
```

### Text-to-Speech API

```
http://localhost:{port}/tts?text=<your_text>&speed=<speed_option>
```

Parameters:

- `text`: Your text in UTF-8 encoding (supports Vietnamese)
- `speed`: Speed of speech generation
  - Available options:
    - `normal`: Standard speaking rate
    - `fast`: Increased speaking rate
    - `slow`: Decreased speaking rate
    - `very_fast`: Maximum speaking rate

Response Format:

```json
{
  "hash": "<unique_identifier>",
  "text": "<input_text>",
  "speed": "<selected_speed>",
  "audio_url": "http://localhost:{port}/audio/<hash>.wav"
}
```

### Audio File Access

```
http://localhost:{port}/audio/<hash>.wav
```

- Returns WAV audio file
- Content-Type: audio/x-wav

### API Documentation

The API is documented using OpenAPI and Swagger UI. You can access the interactive documentation at:

```
http://localhost:{port}/docs
```

The root endpoint (`/`) also redirects to the Swagger UI documentation.

Example Response:

```json
{
  "hash": "e6bc1768c82ae63ed8ee61ca2349efa4ef9f166e",
  "text": "xin chào bạn",
  "speed": "normal",
  "audio_url": "http://localhost:8888/audio/e6bc1768c82ae63ed8ee61ca2349efa4ef9f166e.wav"
}
```

Speed Options:

- ✅ `normal`
- ✅ `fast`
- ✅ `slow`
- ✅ `very_fast`

### Legacy Installation (Not Recommended)

For legacy purposes, you can still install using pip:

```bash
pip install -r requirements.txt
```

Then run the server file:

```bash
python server.py
```

Now, you can access the TTS API with port 8888:

```
http://localhost:8888/tts?text=Xin chào bạn&speed=normal
```

# Development

### Code Quality

The project includes linting and formatting tools:

- **Linting**: `ruff`
- **Formatting**: `black`

Run code quality checks:

```bash
pixi run lint
```

### Testing

The project uses pytest for testing. Run tests with:

```bash
pixi run test
```

### Docker Development

For Docker-based development:

```bash
# Development mode with live reloading
docker-compose up --build

# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

# Result

Audio before finetuning voice (unmute to hear):

<https://github.com/phatjkk/vits-tts-vietnamese/assets/48487157/2a3f51b0-4d27-43a9-b5de-8925ddcc8a2b>

Audio AFTER finetuining voice (unmute to hear):

<https://github.com/phatjkk/vits-tts-vietnamese/assets/48487157/e953f2cc-979d-4fa2-96b2-96786345723d>

### Evaluation

```
### Metrics in test data BEFORE finetuning:
Mean Square Error: (lower is better) 0.04478523858822825
Root Mean Square Error (lower is better): 2.0110066944004297
=============================================
### Metrics in test data AFTER finetuning:
Mean Square Error: (lower is better) 0.043612250527366996
Root Mean Square Error (lower is better): 1.97773962268741
```

In TTS tasks, the output spectrogram for a given text can be represented in many different ways.
So, loss functions like MSE and MAE are just used to encourage the model to minimize the difference between the predicted and target spectrograms.
The right way to Evaluate TTS model is to use MOS(mean opinion scores) BUT it is a subjective scoring system and we need human resources to do it.
Reference: <https://huggingface.co/learn/audio-course/chapter6/evaluation>

# How do we preprocess data and fine-tuning?

See **train_vits.ipynb** file in the repo or via this Google Colab:

<https://colab.research.google.com/drive/1UK6t_AQUw9YJ_RDFvXUJmWMu-oS23XQs?usp=sharing>

ProtonX New: <https://protonx.io/news/hoc-vien-protonx-xay-dung-mo-hinh-chuyen-van-ban-thanh-giong-noi-tieng-viet-1698233526932>

Author: Nguyen Thanh Phat - aka phatjk
