# Finetuining VITS Text-to-Speech Model in Vietnamese

We use Piper library to finetuning VITS for TTS tasks with different voice in Vietnamese.

We also built a Tornado server to deploy TTS model on microservice with Docker.
The server uses ONNX model type to infer lightweight and excellent performance.

Video demo: https://youtu.be/1mAhaP26aQE

Read Project Docs: [Paper](https://github.com/phatjkk/vits-tts-vietnamese/blob/main/TTS_VITS_Docs_NguyenThanhPhat.pdf)

<p align="center">
  <img  src="https://raw.githubusercontent.com/phatjkk/vits-tts-vietnamese/main/resources/web_ui.PNG">
</p>

# How to run this project?

## Prerequisites

- [pixi](https://pixi.sh/) - A fast, cross-platform package manager for Python
- Docker (optional, for containerized deployment)

## Installation with pixi (Recommended)

The project now uses [`pixi.toml`](pixi.toml) for standardized dependency management. This ensures reproducible environments and consistent builds across development and production.

1. Install pixi by following the instructions at https://pixi.sh/

2. Install project dependencies:

   ```bash
   pixi install
   ```

3. Activate the pixi environment:
   ```bash
   pixi shell
   ```

## Configuration

The application uses a [`config.yaml`](config.yaml) file for configuration. This allows you to customize various aspects of the application without modifying the code.

### Configuration File (`config.yaml`)

The configuration file is located at [`config.yaml`](config.yaml) and contains the following sections:

#### Server Configuration

```yaml
server:
  port: 8888 # Port for the TTS server
  cors_origins: # Allowed CORS origins
    - "http://localhost:3000"
    - "http://127.0.0.1:3000"
```

#### TTS Configuration

```yaml
tts:
  model_path: "fine-tuning-model/v2/finetuning_pretrained_vi.onnx" # Path to the ONNX model
  config_path: "fine-tuning-model/v2/finetuning_pretrained_vi.onnx.json" # Path to model config
  audio_output_dir: "audio/" # Directory for saving generated audio files
```

#### Logging Configuration

```yaml
logging:
  level: "INFO" # Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Modifying Configuration

To modify the configuration:

1. Edit the [`config.yaml`](config.yaml) file directly
2. The application will automatically pick up changes on restart

## Usage

### Running the Server

With the pixi environment activated:

```bash
pixi run server
```

Or, if you prefer to run directly:

```bash
python server.py
```

The server will start on port 8888 by default (as specified in [`config.yaml`](config.yaml:2)).

### With Docker (**_highly recommend_**):

On your terminal, type these commands to build a Docker Image:

```
docker build  ./ -f .Dockerfile -t vits-tts-vi:v1.0
```

Then run it with port 5004:

```
docker run -d -p 5004:8888 vits-tts-vi:v1.0
```

While the Docker Image was running, you now make a request to use the TTS task via this API on your browser.

```
http://localhost:5004/tts?text=Xin chào bạn&speed=normal
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

The result seems like this:

<p align="center">
  <img  src="https://raw.githubusercontent.com/phatjkk/vits-tts-vietnamese/main/resources/demo_api.PNG">
</p>

```json
{
  "hash": "e6bc1768c82ae63ed8ee61ca2349efa4ef9f166e",
  "text": "xin chào bạn",
  "speed": "normal",
  "audio_url": "http://localhost:5004/audio/e6bc1768c82ae63ed8ee61ca2349efa4ef9f166e.wav"
}
```

The speed has 5 options:

- ✅ `normal`
- ✅ `fast`
- ✅ `slow`
- ✅ `very_fast`

Or you can use the Web UI via this URL:

```
http://localhost:5004/
```

The repo of this React Front-end: [vits-tts-webapp](https://github.com/phatjkk/vits-tts-webapp)

<p align="center">
  <img  src="https://raw.githubusercontent.com/phatjkk/vits-tts-vietnamese/main/resources/web_ui.PNG">
</p>

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

The result also seems like this:

```json
{
  "hash": "e6bc1768c82ae63ed8ee61ca2349efa4ef9f166e",
  "text": "xin chào bạn",
  "speed": "normal",
  "audio_url": "http://localhost:5004/audio/e6bc1768c82ae63ed8ee61ca2349efa4ef9f166e.wav"
}
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

# Result

Audio before finetuning voice (unmute to hear):

https://github.com/phatjkk/vits-tts-vietnamese/assets/48487157/2a3f51b0-4d27-43a9-b5de-8925ddcc8a2b

Audio AFTER finetuining voice (unmute to hear):

https://github.com/phatjkk/vits-tts-vietnamese/assets/48487157/e953f2cc-979d-4fa2-96b2-96786345723d

### Evaluation:

```
### Metrics in test data BEFORE finetuning:
Mean Square Error: (lower is better) 0.044785238588228825
Root Mean Square Error (lower is better): 2.0110066944004297
=============================================
### Metrics in test data AFTER finetuning:
Mean Square Error: (lower is better) 0.043612250527366996
Root Mean Square Error (lower is better): 1.97773962268741
```

In TTS tasks, the output spectrogram for a given text can be represented in many different ways.
So, loss functions like MSE and MAE are just used to encourage the model to minimize the difference between the predicted and target spectrograms.
The right way to Evaluate TTS model is to use MOS(mean opinion scores) BUT it is a subjective scoring system and we need human resources to do it.
Reference: https://huggingface.co/learn/audio-course/chapter6/evaluation

# How do we preprocess data and fine-tuning?

See **train_vits.ipynb** file in the repo or via this Google Colab:

https://colab.research.google.com/drive/1UK6t_AQUw9YJ_RDFvXUJmWMu-oS23XQs?usp=sharing

ProtonX New: https://protonx.io/news/hoc-vien-protonx-xay-dung-mo-hinh-chuyen-van-ban-thanh-giong-noi-tieng-viet-1698233526932

Author: Nguyen Thanh Phat - aka phatjk
