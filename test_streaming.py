#!/usr/bin/env python3
"""
Test script for the streaming TTS functionality
"""

import sys
import os
sys.path.append('.')

from tts import text_to_speech_streaming
import io
import requests

def test_streaming_function():
    """Test the text_to_speech_streaming function"""
    print("Testing text_to_speech_streaming function...")
    
    try:
        # Test with simple text
        text = "Xin chào thế giới"
        speed = "normal"
        model_name = "pretrained_vi.onnx"
        
        print(f"Generating audio for text: '{text}' with speed: {speed}")
        
        # Call the streaming function
        audio_buffer = text_to_speech_streaming(text, speed, model_name)
        
        # Check if we got a BytesIO buffer
        if isinstance(audio_buffer, io.BytesIO):
            print("✓ Successfully generated audio buffer")
            
            # Check the size of the audio data
            audio_buffer.seek(0, io.SEEK_END)
            size = audio_buffer.tell()
            audio_buffer.seek(0)  # Reset position
            
            print(f"✓ Audio buffer size: {size} bytes")
            
            # Check if it starts with WAV header
            header = audio_buffer.read(4)
            audio_buffer.seek(0)  # Reset position
            
            if header == b'RIFF':
                print("✓ Valid WAV header detected")
            else:
                print("✗ Invalid WAV header")
                
            # Try to read some data
            sample_data = audio_buffer.read(100)
            audio_buffer.seek(0)  # Reset position
            
            if len(sample_data) > 0:
                print("✓ Successfully read audio data from buffer")
            else:
                print("✗ No audio data in buffer")
                
            return True
        else:
            print("✗ Function did not return a BytesIO buffer")
            return False
            
    except Exception as e:
        print(f"✗ Error during streaming test: {e}")
        return False

def test_server_endpoint():
    """Test the server endpoint (if server is running)"""
    print("\nTesting server endpoint...")
    
    try:
        import time
        
        # Test parameters
        text = "Xin chào"
        speed = "normal"
        
        # Construct URL
        url = f"http://localhost:8889/tts/stream?text={text}&speed={speed}"
        
        print(f"Testing URL: {url}")
        
        # Make request with streaming
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            print(f"✓ Server responded with status {response.status_code}")
            print(f"✓ Content-Type: {response.headers.get('Content-Type', 'Not set')}")
            
            # Read first few chunks to verify streaming
            total_bytes = 0
            chunk_count = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    total_bytes += len(chunk)
                    chunk_count += 1
                    if chunk_count >= 3:  # Just test first few chunks
                        break
            
            print(f"✓ Received {total_bytes} bytes in {chunk_count} chunks")
            
            if total_bytes > 0:
                print("✓ Streaming endpoint is working!")
                return True
            else:
                print("✗ No data received from streaming endpoint")
                return False
        else:
            print(f"✗ Server responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server on port 8889")
        print("  Make sure the server is running with: pixi run python server.py --no-ui")
        return False
    except ImportError:
        print("✗ requests module not available, skipping server test")
        return False
    except Exception as e:
        print(f"✗ Error testing server endpoint: {e}")
        return False

if __name__ == "__main__":
    print("=== Streaming TTS Test Suite ===\n")
    
    # Test 1: Function level test
    function_test_passed = test_streaming_function()
    
    # Test 2: Server endpoint test (if possible)
    server_test_passed = test_server_endpoint()
    
    print("\n=== Test Results ===")
    print(f"Function test: {'PASSED' if function_test_passed else 'FAILED'}")
    print(f"Server test: {'PASSED' if server_test_passed else 'FAILED'}")
    
    if function_test_passed:
        print("\n✓ Streaming functionality is working correctly!")
        print("  To test the full endpoint, run the server with:")
        print("  pixi run python server.py --no-ui")
        print("  Then visit: http://localhost:8888/tts/stream?text=Xin%20chào&speed=normal")
    else:
        print("\n✗ Streaming functionality has issues that need to be fixed.")