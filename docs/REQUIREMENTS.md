# Requirements

## Functional Requirements

- **FR1: Text-to-Speech Conversion:** The system must be able to convert Vietnamese text into speech.
- **FR2: Speech Speed Control:** The user must be able to control the speed of the generated speech (e.g., normal, fast, slow).
- **FR3: Web API:** The system must provide a RESTful API for TTS conversion.
    - **FR3.1:** The API must accept text and speed as input parameters.
    - **FR3.2:** The API must return a JSON response containing a URL to the generated audio file.
- **FR4: Web UI:** The system must provide a web-based user interface for interacting with the TTS service.
    - **FR4.1:** The UI must have a text input field.
    - **FR4.2:** The UI must have an option to select the speech speed.
    - **FR4.3:** The UI must be able to play the generated audio.

## Non-Functional Requirements

- **NFR1: Performance:** The TTS conversion should be fast enough for real-time or near-real-time use.
- **NFR2: Scalability:** The system should be scalable to handle multiple concurrent requests.
- **NFR3: Deployability:** The system must be easy to deploy and manage, preferably using Docker.
- **NFR4: Model Format:** The TTS model should be in ONNX format for efficient inference.
