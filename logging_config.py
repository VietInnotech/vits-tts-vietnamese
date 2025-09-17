"""
Structured logging configuration using loguru.
This module configures loguru for JSON output and integrates with application settings.
"""

import sys
from loguru import logger as loguru_logger
from config import get_logging_config


def configure_logger():
    """
    Configure loguru logger with default format for stdout and file.
    Console output will be colorized, file output will not.

    Returns:
        Configured logger instance
    """
    # Get logging configuration from config
    logging_config = get_logging_config()
    log_level = logging_config.get("level", "INFO")

    # Remove default handler to avoid duplicate logs
    loguru_logger.remove()

    # Add handler to stdout with default format and colorization
    loguru_logger.add(
        sys.stdout,
        level=log_level,
        colorize=True,  # Enable colorization for console
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for persistent logging with default format (no colors)
    loguru_logger.add(
        "logs/tts_server.log",
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
