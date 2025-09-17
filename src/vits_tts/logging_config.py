import logging
import logging.config
from pathlib import Path
from typing import Dict, Any

# Default logging configuration
DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "data/logs/tts_server.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "tts_server": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Global logger instance
logger = logging.getLogger("tts_server")


def setup_logging(config: Dict[str, Any] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        config: Logging configuration dictionary. If None, uses default config.
    """
    if config is None:
        config = DEFAULT_LOGGING_CONFIG
    
    # Ensure logs directory exists
    log_file_path = config.get("handlers", {}).get("file", {}).get("filename")
    if log_file_path:
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.config.dictConfig(config)
    
    # Log initial message
    logger.info(
        "Logging configured",
        extra={
            "log_level": logging.getLevelName(logger.level),
            "log_file": log_file_path,
        },
    )


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Name of the logger. If None, returns the root TTS server logger.
        
    Returns:
        Logger instance
    """
    if name is None:
        return logger
    return logging.getLogger(name)


def update_log_level(level: str) -> None:
    """
    Update the logging level for the TTS server logger.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logger.setLevel(numeric_level)
    logger.info(f"Log level changed to {level.upper()}")


# Initialize logging on module import
try:
    # Try to load logging config from main config file
    from .config import get_config
    
    config = get_config()
    logging_config = config.get("logging", DEFAULT_LOGGING_CONFIG)
    setup_logging(logging_config)
    
except ImportError:
    # If config module is not available, use default config
    setup_logging(DEFAULT_LOGGING_CONFIG)
    logger.warning("Could not import config module, using default logging configuration")
except Exception as e:
    # If any other error occurs, use default config
    setup_logging(DEFAULT_LOGGING_CONFIG)
    logger.error(f"Error setting up logging: {e}, using default configuration")