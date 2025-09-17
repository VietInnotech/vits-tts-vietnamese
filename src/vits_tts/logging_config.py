"""Loguru-based logging configuration for the TTS service.
Enables colored console output and intercepts standard logging to preserve ANSI colors.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger as loguru_logger

try:
    from .config import get_logging_config
except Exception:
    def get_logging_config() -> Dict[str, Any]:
        return {
            "level": "INFO",
            "console": {"color": True},
            "file": {"path": "data/logs/tts_server.log"},
        }


def _ensure_log_dir(path: str) -> None:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


class InterceptHandler(logging.Handler):
    """
    Redirect stdlib logging records to loguru while preserving message content
    (including ANSI color sequences) so the console sink renders colors.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = record.levelname
        except Exception:
            level = record.levelno

        # Calculate stack depth so loguru attributes the log to the original caller
        frame = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Use record.getMessage() to preserve any ANSI color codes present
        loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure loguru sinks (colored console + JSON file) and intercept the
    standard logging module so third-party libraries' logs flow through loguru.
    """
    if config is None:
        try:
            config = get_logging_config()
        except Exception:
            config = {
                "level": "INFO",
                "console": {"color": True},
                "file": {"path": "data/logs/tts_server.log"},
            }

    level = config.get("level", "INFO")
    console_cfg = config.get("console", {})
    file_cfg = config.get("file", {})

    # Remove any existing loguru handlers before reconfiguring
    loguru_logger.remove()

    # Console sink (colorized)
    colorize = bool(console_cfg.get("color", True))
    console_format = console_cfg.get(
        "format",
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    loguru_logger.add(
        sys.stdout,
        colorize=colorize,
        format=console_format,
        level=level,
        backtrace=True,
        diagnose=True,
    )

    # File sink (JSON)
    file_path = file_cfg.get("path", "data/logs/tts_server.log")
    _ensure_log_dir(file_path)
    loguru_logger.add(
        file_path,
        serialize=True,
        level=level,
        rotation=file_cfg.get("rotation", "10 MB"),
        retention=file_cfg.get("retention", "7 days"),
        compression=file_cfg.get("compression", "zip"),
        backtrace=True,
        diagnose=True,
    )

    # Replace stdlib handlers with our intercept handler
    intercept_handler = InterceptHandler()
    logging.root.handlers = [intercept_handler]
    logging.root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Ensure existing loggers propagate to root to avoid duplicate stdlib handlers
    for name, logger_obj in list(logging.Logger.manager.loggerDict.items()):
        try:
            if isinstance(logger_obj, logging.Logger):
                logger_obj.handlers = []
                logger_obj.propagate = True
        except Exception:
            pass

    loguru_logger.bind(component="logging").info("Logging configured", level=level, log_file=file_path)


def get_logger(name: Optional[str] = None):
    """
    Return a Loguru logger or a bound logger with a name for compatibility.
    """
    if name:
        return loguru_logger.bind(logger_name=name)
    return loguru_logger


def update_log_level(level: str) -> None:
    """
    Update logging level by re-running setup with the new level (best-effort).
    """
    logging.root.setLevel(getattr(logging, level.upper(), logging.INFO))
    try:
        cfg = {}
        try:
            cfg = get_logging_config()
        except Exception:
            cfg = {"level": level}
        cfg["level"] = level
        setup_logging(cfg)
    except Exception:
        loguru_logger.warning("Failed to update logging level via setup; leaving current configuration in place")


# Auto-configure on import; safe best-effort
try:
    setup_logging(get_logging_config())
except Exception:
    try:
        setup_logging()
    except Exception:
        logging.basicConfig(level=logging.INFO)
# Export logger for backward compatibility
logger = loguru_logger