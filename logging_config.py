"""
Structured logging configuration using loguru.
This module configures loguru for JSON output and integrates with application settings.
"""

import sys
from loguru import logger as loguru_logger
from config import get_logging_config


def configure_logger():
    """
    Configure loguru logger with JSON format and settings from config.yaml.

    Returns:
        Configured logger instance
    """
    # Get logging configuration from config
    logging_config = get_logging_config()
    log_level = logging_config.get("level", "INFO")

    # Remove default handler to avoid duplicate logs
    loguru_logger.remove()

    # Add JSON formatted handler to stdout
    loguru_logger.add(
        sys.stdout,
        format="{time} | {level} | {name} | {function} | {line} | {message}",
        serialize=True,  # Enable JSON serialization
        level=log_level,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for persistent logging
    loguru_logger.add(
        "logs/tts_server.log",
        format="{time} | {level} | {name} | {function} | {line} | {message}",
        serialize=True,
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    return loguru_logger


# Configure and export the logger
logger = configure_logger()
