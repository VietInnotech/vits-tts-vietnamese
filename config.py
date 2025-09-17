import yaml
import os
from typing import Dict, Any

# Global settings variable
settings: Dict[str, Any] = {}

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing the loaded configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    global settings
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            settings = yaml.safe_load(file)
        return settings
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML configuration: {e}")

def get_config() -> Dict[str, Any]:
    """
    Get the loaded configuration.
    
    Returns:
        Dictionary containing the configuration settings
    """
    global settings
    if not settings:
        load_config()
    return settings

def get_server_config() -> Dict[str, Any]:
    """Get server configuration section."""
    config = get_config()
    return config.get('server', {})

def get_tts_config() -> Dict[str, Any]:
    """Get TTS configuration section."""
    config = get_config()
    return config.get('tts', {})

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration section."""
    config = get_config()
    return config.get('logging', {})

# Load configuration on module import
try:
    load_config()
except Exception as e:
    print(f"Warning: Failed to load configuration: {e}")
    # Set default values if config loading fails
    settings = {
        'server': {
            'port': 8888,
            'cors_origins': ["http://localhost:3000", "http://127.0.0.1:3000"]
        },
        'tts': {
            'model_path': "fine-tuning-model/v2/finetuning_pretrained_vi.onnx",
            'config_path': "fine-tuning-model/v2/finetuning_pretrained_vi.onnx.json",
            'audio_output_dir': "audio/"
        },
        'logging': {
            'level': "INFO"
        }
    }