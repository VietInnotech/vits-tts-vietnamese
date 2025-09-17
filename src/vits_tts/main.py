import tornado.ioloop
import tornado.web
import tornado.gen
from .validate import validate_query_params
from .tts import text_to_speech, text_to_speech_streaming
import hashlib
import os
import sys
import argparse
from .config import get_server_config, get_tts_config, get_logging_config
from .logging_config import logger
from cachetools import LRUCache

# Initialize in-memory LRU cache with maxsize of 128 items
audio_cache = LRUCache(maxsize=128)

# Define a JSON schema for your query parameters
query_param_schema = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "speed": {"type": "string", "maxLength": 9},
    },
    "required": ["text", "speed"],
}


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("web/index.html")


class MyHandler(tornado.web.RequestHandler):
    @validate_query_params(query_param_schema)
    def get(self):
        # Parameters are already validated here
        text: str = self.get_argument("text")
        speed: str = self.get_argument("speed")
        current_url: str = "{}://{}".format(self.request.protocol, self.request.host)

        logger.info(
            "TTS request received",
            extra={
                "text_length": len(text),
                "speed": speed,
                "client_ip": self.request.remote_ip,
                "endpoint": "/tts",
            },
        )

        result, file_name = handle_tts_request(text, speed)
        result["audio_url"] = current_url + "/audio/" + file_name
        self.write(result)

    def set_default_headers(self):
        server_config = get_server_config()
        cors_origins = server_config.get("cors_origins", ["*"])
        # For simplicity, we'll use the first CORS origin or "*" if none specified
        cors_origin = cors_origins[0] if cors_origins else "*"
        self.set_header("Access-Control-Allow-Origin", cors_origin)
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")


class StreamingTTSHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    @validate_query_params(query_param_schema)
    def get(self):
        # Parameters are already validated here
        text: str = self.get_argument("text")
        speed: str = self.get_argument("speed")

        logger.info(
            "Streaming TTS request received",
            extra={
                "text_length": len(text),
                "speed": speed,
                "client_ip": self.request.remote_ip,
                "endpoint": "/tts/stream",
            },
        )

        # Set appropriate headers for audio streaming
        self.set_header("Content-Type", "audio/wav")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Pragma", "no-cache")

        try:
            # Get TTS configuration
            tts_config = get_tts_config()
            model_path = tts_config.get("model_path", "models/pretrained_vi.onnx")
            
            # Create cache key for streaming audio
            cache_key = f"stream:{hashlib.sha1((text + speed).encode('utf-8')).hexdigest()}"
            
            # Check if audio data is in cache
            if cache_key in audio_cache:
                logger.info(
                    "Streaming TTS cache hit",
                    extra={
                        "cache_key": cache_key,
                        "text_length": len(text),
                        "speed": speed,
                    },
                )
                audio_buffer = audio_cache[cache_key]
                # Reset buffer position for streaming
                audio_buffer.seek(0)
            else:
                logger.info(
                    "Streaming TTS cache miss - generating new audio",
                    extra={
                        "cache_key": cache_key,
                        "text_length": len(text),
                        "speed": speed,
                    },
                )
                # Generate audio data using the streaming function
                audio_buffer = text_to_speech_streaming(text, speed, model_path)
                
                # Store in cache for future use
                audio_buffer.seek(0)  # Reset position before caching
                audio_cache[cache_key] = audio_buffer
                audio_buffer.seek(0)  # Reset position again for streaming

            logger.debug(
                "Audio streaming started",
                extra={
                    "text_length": len(text),
                    "speed": speed,
                    "model_path": model_path,
                    "cache_key": cache_key,
                },
            )

            # Stream the audio data in chunks
            chunk_size = 8192  # 8KB chunks
            chunks_sent = 0
            while True:
                chunk = audio_buffer.read(chunk_size)
                if not chunk:
                    break
                self.write(chunk)
                yield self.flush()  # Ensure data is sent immediately
                chunks_sent += 1

            # Finish the response
            self.finish()
            logger.info(
                "Audio streaming completed",
                extra={
                    "text_length": len(text),
                    "speed": speed,
                    "chunks_sent": chunks_sent,
                    "cache_key": cache_key,
                },
            )

        except Exception as e:
            logger.error(
                "Error during audio streaming",
                extra={
                    "error": str(e),
                    "text_length": len(text),
                    "speed": speed,
                    "client_ip": self.request.remote_ip,
                },
            )
            self.set_status(500)
            self.write({"error": str(e)})
            self.finish()

    def set_default_headers(self):
        server_config = get_server_config()
        cors_origins = server_config.get("cors_origins", ["*"])
        # For simplicity, we'll use the first CORS origin or "*" if none specified
        cors_origin = cors_origins[0] if cors_origins else "*"
        self.set_header("Access-Control-Allow-Origin", cors_origin)
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")


def make_app(enable_ui=True):
    tts_config = get_tts_config()
    audio_output_dir = tts_config.get("audio_output_dir", "audio/")

    handlers = [
        (r"/tts", MyHandler),
        (r"/tts/stream", StreamingTTSHandler),
        (
            r"/audio/(.*)",
            tornado.web.StaticFileHandler,
            {"path": os.getcwd() + "/" + audio_output_dir},
        ),
        (
            r"/assets/(.*)",
            tornado.web.StaticFileHandler,
            {"path": os.getcwd() + "/assets/"},
        ),
    ]

    if enable_ui:
        handlers.append((r"/", HomeHandler))

    return tornado.web.Application(handlers)


def handle_tts_request(text, speed):
    tts_config = get_tts_config()
    audio_output_dir = tts_config.get("audio_output_dir", "audio/")
    model_path = tts_config.get("model_path", "models/pretrained_vi.onnx")

    text_hash: str = hashlib.sha1((text + speed).encode("utf-8")).hexdigest()
    file_name = text_hash + ".wav"
    file_path = os.getcwd() + "/" + audio_output_dir + file_name

    # Create cache key for file-based audio
    cache_key = f"file:{text_hash}"
    
    # Check if result is in memory cache first
    if cache_key in audio_cache:
        logger.info(
            "TTS memory cache hit",
            extra={
                "cache_key": cache_key,
                "text_hash": text_hash,
                "text_length": len(text),
                "speed": speed,
                "file_path": file_path,
            },
        )
        return (
            {
                "hash": text_hash,
                "text": text,
                "speed": speed,
            },
            file_name,
        )
    
    # Check if file exists (filesystem cache)
    if os.path.isfile(file_path):
        logger.info(
            "TTS filesystem cache hit",
            extra={
                "cache_key": cache_key,
                "text_hash": text_hash,
                "text_length": len(text),
                "speed": speed,
                "file_path": file_path,
            },
        )
        # Store in memory cache for faster future access
        audio_cache[cache_key] = True
        return (
            {
                "hash": text_hash,
                "text": text,
                "speed": speed,
            },
            file_name,
        )
    else:
        logger.info(
            "TTS cache miss - generating new audio",
            extra={
                "cache_key": cache_key,
                "text_hash": text_hash,
                "text_length": len(text),
                "speed": speed,
                "model_path": model_path,
            },
        )
        try:
            # create new file
            text_to_speech(text, speed, model_path, text_hash)
            logger.info(
                "TTS audio generation completed",
                extra={
                    "cache_key": cache_key,
                    "text_hash": text_hash,
                    "text_length": len(text),
                    "speed": speed,
                    "file_path": file_path,
                },
            )
            # Store in memory cache
            audio_cache[cache_key] = True
        except Exception as e:
            logger.error(
                "TTS audio generation failed",
                extra={
                    "error": str(e),
                    "cache_key": cache_key,
                    "text_hash": text_hash,
                    "text_length": len(text),
                    "speed": speed,
                    "model_path": model_path,
                },
            )
            raise

        return (
            {
                "hash": text_hash,
                "text": text,
                "speed": speed,
            },
            file_name,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TTS Server")
    parser.add_argument(
        "--no-ui", action="store_true", help="Disable the web interface"
    )
    args = parser.parse_args()

    logger.info(
        "TTS Server starting up",
        extra={"ui_enabled": not args.no_ui, "python_version": sys.version},
    )

    app = make_app(enable_ui=not args.no_ui)
    server_config = get_server_config()
    port = server_config.get("port", 8888)

    logger.info(
        "Server configuration loaded",
        extra={
            "port": port,
            "cors_origins": server_config.get("cors_origins", []),
            "audio_output_dir": get_tts_config().get("audio_output_dir"),
            "model_path": get_tts_config().get("model_path"),
            "log_level": get_logging_config().get("level"),
            "cache_maxsize": 128,
        },
    )

    app.listen(port)
    logger.info(
        "TTS Server started successfully",
        extra={"port": port, "ui_enabled": not args.no_ui},
    )
    tornado.ioloop.IOLoop.current().start()
