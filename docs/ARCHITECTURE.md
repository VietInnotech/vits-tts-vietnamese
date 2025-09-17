# Architecture

## Components

### 1. TTS Model

- **Description:** A fine-tuned VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech) model for Vietnamese.
- **Format:** ONNX for lightweight and efficient inference.
- **Responsibilities:** Converts text into speech (waveform).
- **Dependencies:** Piper library for fine-tuning.

### 2. Web Server

- **Description:** A Tornado-based web server that exposes the TTS model through a RESTful API.
- **Responsibilities:**
  - Handles incoming HTTP requests.
  - Validates input parameters (text and speed).
  - Calls the TTS model to generate audio.
  - Saves the generated audio to a file.
  - Returns a JSON response with a link to the audio file.
- **Dependencies:** Tornado framework.

### 3. Web UI

- **Description:** A simple web-based user interface for interacting with the TTS service.
- **Responsibilities:**
  - Provides a text input for the user.
  - Allows the user to select the speech speed.
  - Displays the generated audio for playback.
- **Dependencies:** React (from the README, the UI is in a separate repo).

### 4. Docker Container

- **Description:** A Docker container that packages the entire application (web server and TTS model) for easy deployment.
- **Responsibilities:**
  - Provides a consistent and isolated environment for the application.
  - Simplifies deployment and scaling.
- **Dependencies:** Docker.

## API Endpoints

### `/tts/stream` - Stream Audio

This endpoint converts text to speech and streams the resulting audio data directly to the client without writing to the filesystem.

- **URL:** `/tts/stream`
- **Method:** `GET`
- **Query Parameters:**
  - `text` (string, required): The text to be converted to speech.
  - `speed` (string, required): The desired speech speed. Valid options are: `very_slow`, `slow`, `normal`, `fast`, `very_fast`.
- **Success Response:**
  - **Code:** `200 OK`
  - **Content-Type:** `audio/wav`
  - **Body:** The raw WAV audio data.
- **Error Response:**
  - **Code:** `400 Bad Request`
  - **Content-Type:** `application/json`
  - **Body:** A JSON object containing an error message (e.g., `{"error": "Invalid speed parameter."}`).
- **Implementation Details:**
  - The endpoint is handled by the `StreamingTTSHandler` in [`server.py`](server.py).
  - It uses Tornado's asynchronous features (`@tornado.gen.coroutine`) to stream the audio data in chunks.
  - The audio is generated in-memory by the `text_to_speech_streaming` function in [`tts.py`](tts.py), which uses a `BytesIO` buffer. This avoids writing to the filesystem.

## Deployment

The application is designed to be deployed as a microservice using Docker. The `Dockerfile` and `run_docker_image_cmd.txt` provide instructions for building and running the Docker container.

The service runs on port 8888 inside the container, which is mapped to a port on the host machine (e.g., 5004 in the example).
