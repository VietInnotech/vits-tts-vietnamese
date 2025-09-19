import os
import sys
import tempfile
import yaml
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, 'src')

from vits_tts.config import load_config, get_tts_config, get_server_config, get_logging_config

def test_environment_variable_overrides():
    """Test that environment variables override configuration values."""
    
    # Create a temporary config file
    config_data = {
        'server': {
            'port': 8888
        },
        'tts': {
            'model_path': 'models/v2/finetuning_pretrained_vi.onnx',
            'config_path': 'models/v2/finetuning_pretrained_vi.onnx.json',
            'audio_output_dir': 'audio/',
            'cache_size': 100,
            'default_speed': 'normal',
            'noise_scale': 0.4,
            'noise_w': 0.5
        },
        'logging': {
            'level': 'INFO'
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        # Test with environment variables
        env_vars = {
            'SERVER_PORT': '9000',
            'TTS_MODEL_PATH': 'models/infore/vi_VN-vais1000-medium.onnx',
            'TTS_CONFIG_PATH': 'models/infore/vi_VN-vais1000-medium.onnx.json',
            'TTS_AUDIO_OUTPUT_DIR': 'output/',
            'TTS_CACHE_SIZE': '200',
            'TTS_DEFAULT_SPEED': 'fast',
            'TTS_NOISE_SCALE': '0.6',
            'TTS_NOISE_W': '0.7',
            'LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config(config_path)
            
            # Test server config
            server_config = get_server_config()
            assert server_config['port'] == 9000, f"Expected port 9000, got {server_config['port']}"
            
            # Test TTS config
            tts_config = get_tts_config()
            assert tts_config['model_path'] == 'models/infore/vi_VN-vais1000-medium.onnx'
            assert tts_config['config_path'] == 'models/infore/vi_VN-vais1000-medium.onnx.json'
            assert tts_config['audio_output_dir'] == 'output/'
            assert tts_config['cache_size'] == 200
            assert tts_config['default_speed'] == 'fast'
            assert tts_config['noise_scale'] == 0.6
            assert tts_config['noise_w'] == 0.7
            
            # Test logging config
            logging_config = get_logging_config()
            assert logging_config['level'] == 'DEBUG'
            
        print("✅ All environment variable override tests passed!")
        
        # Test with partial environment variables
        partial_env_vars = {
            'TTS_MODEL_PATH': 'models/infore/vi_VN-vais1000-medium.onnx',
            'SERVER_PORT': 'invalid_port'  # This should be ignored
        }
        
        with patch.dict(os.environ, partial_env_vars):
            config = load_config(config_path)
            
            # Test that invalid port is ignored
            server_config = get_server_config()
            assert server_config['port'] == 8888, f"Expected port 8888, got {server_config['port']}"
            
            # Test that model path is overridden
            tts_config = get_tts_config()
            assert tts_config['model_path'] == 'models/infore/vi_VN-vais1000-medium.onnx'
            
        print("✅ Partial environment variable override tests passed!")
        
    finally:
        # Clean up temporary file
        os.unlink(config_path)

if __name__ == '__main__':
    test_environment_variable_overrides()
    print("🎉 All tests passed successfully!")