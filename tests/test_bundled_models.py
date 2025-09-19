import os
import sys

# Add src to path for imports
sys.path.insert(0, 'src')

def test_model_files_exist():
    """Test that bundled model files exist in the expected locations."""
    
    # Check InfoRE model files
    infore_model_path = 'models/infore/vi_VN-vais1000-medium.onnx'
    infore_config_path = 'models/infore/vi_VN-vais1000-medium.onnx.json'
    
    assert os.path.exists(infore_model_path), f"InfoRE model file not found: {infore_model_path}"
    assert os.path.exists(infore_config_path), f"InfoRE config file not found: {infore_config_path}"
    
    # Check V2 model files
    v2_model_path = 'models/v2/finetuning_pretrained_vi.onnx'
    v2_config_path = 'models/v2/finetuning_pretrained_vi.onnx.json'
    
    assert os.path.exists(v2_model_path), f"V2 model file not found: {v2_model_path}"
    assert os.path.exists(v2_config_path), f"V2 config file not found: {v2_config_path}"
    
    print("✅ All bundled model files exist!")

def test_model_file_sizes():
    """Test that model files have reasonable sizes (not empty)."""
    
    # Check InfoRE model files
    infore_model_size = os.path.getsize('models/infore/vi_VN-vais1000-medium.onnx')
    infore_config_size = os.path.getsize('models/infore/vi_VN-vais1000-medium.onnx.json')
    
    assert infore_model_size > 1000000, f"InfoRE model file too small: {infore_model_size} bytes"
    assert infore_config_size > 100, f"InfoRE config file too small: {infore_config_size} bytes"
    
    # Check V2 model files
    v2_model_size = os.path.getsize('models/v2/finetuning_pretrained_vi.onnx')
    v2_config_size = os.path.getsize('models/v2/finetuning_pretrained_vi.onnx.json')
    
    assert v2_model_size > 1000000, f"V2 model file too small: {v2_model_size} bytes"
    assert v2_config_size > 100, f"V2 config file too small: {v2_config_size} bytes"
    
    print(f"✅ InfoRE model size: {infore_model_size:,} bytes")
    print(f"✅ InfoRE config size: {infore_config_size:,} bytes")
    print(f"✅ V2 model size: {v2_model_size:,} bytes")
    print(f"✅ V2 config size: {v2_config_size:,} bytes")

if __name__ == '__main__':
    test_model_files_exist()
    test_model_file_sizes()
    print("🎉 All bundled model tests passed successfully!")