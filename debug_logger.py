import sys
import os

# Add the current directory to sys.path to ensure logging_config can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    print("Attempting to import logging_config...")
    from logging_config import logger
    print("Successfully imported logging_config.")
    print("Attempting to log a test message...")
    logger.info("This is a test message to verify logger functionality and format.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    print("Logging test complete.")
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
