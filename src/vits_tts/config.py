import yaml
import os
from typing import Dict, Any

# Global settings variable
settings: Dict[str, Any] = {}

def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable overrides.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing the loaded configuration with environment overrides
        
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
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML configuration: {e}")
    
    # Apply environment variable overrides
    apply_environment_overrides()
    
    return settings

def apply_environment_overrides():
    """Apply environment variable overrides to the configuration."""
    global settings
    
    # Server configuration overrides
    if 'server' not in settings:
        settings['server'] = {}
    
    server_port = os.getenv('SERVER_PORT')
    if server_port is not None:
        try:
            settings['server']['port'] = int(server_port)
        except ValueError:
            print(f"Warning: Invalid SERVER_PORT value '{server_port}', ignoring.")
    
    # TTS configuration overrides
    if 'tts' not in settings:
        settings['tts'] = {}
    
    tts_model_path = os.getenv('TTS_MODEL_PATH')
    if tts_model_path is not None:
        settings['tts']['model_path'] = tts_model_path
    
    tts_config_path = os.getenv('TTS_CONFIG_PATH')
    if tts_config_path is not None:
        settings['tts']['config_path'] = tts_config_path
    
    tts_audio_output_dir = os.getenv('TTS_AUDIO_OUTPUT_DIR')
    if tts_audio_output_dir is not None:
        settings['tts']['audio_output_dir'] = tts_audio_output_dir
    
    tts_cache_size = os.getenv('TTS_CACHE_SIZE')
    if tts_cache_size is not None:
        try:
            settings['tts']['cache_size'] = int(tts_cache_size)
        except ValueError:
            print(f"Warning: Invalid TTS_CACHE_SIZE value '{tts_cache_size}', ignoring.")
    
    tts_default_speed = os.getenv('TTS_DEFAULT_SPEED')
    if tts_default_speed is not None:
        settings['tts']['default_speed'] = tts_default_speed
    
    tts_noise_scale = os.getenv('TTS_NOISE_SCALE')
    if tts_noise_scale is not None:
        try:
            settings['tts']['noise_scale'] = float(tts_noise_scale)
        except ValueError:
            print(f"Warning: Invalid TTS_NOISE_SCALE value '{tts_noise_scale}', ignoring.")
    
    tts_noise_w = os.getenv('TTS_NOISE_W')
    if tts_noise_w is not None:
        try:
            settings['tts']['noise_w'] = float(tts_noise_w)
        except ValueError:
            print(f"Warning: Invalid TTS_NOISE_W value '{tts_noise_w}', ignoring.")
    
    # Logging configuration overrides
    if 'logging' not in settings:
        settings['logging'] = {}
    
    log_level = os.getenv('LOG_LEVEL')
    if log_level is not None:
        settings['logging']['level'] = log_level

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
            'model_path': "models/fine-tuning-model/v2/finetuning_pretrained_vi.onnx",
            'config_path': "models/fine-tuning-model/v2/finetuning_pretrained_vi.onnx.json",
            'audio_output_dir': "audio/"
        },
        'logging': {
            'level': "INFO"
        }
    }
    # Apply environment variable overrides to defaults as well
    apply_environment_overrides()