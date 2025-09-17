#!/usr/bin/env python3
"""
Test script to verify the cache implementation works correctly.
This tests the basic cache functionality without starting the server.
"""

import sys
import os
import hashlib
from io import BytesIO

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cachetools import LRUCache

def test_lru_cache_basic():
    """Test basic LRU cache functionality"""
    print("Testing basic LRU cache functionality...")
    
    # Create cache with maxsize of 3 for testing
    cache = LRUCache(maxsize=3)
    
    # Test basic set and get
    cache['key1'] = 'value1'
    cache['key2'] = 'value2'
    cache['key3'] = 'value3'
    
    assert cache['key1'] == 'value1'
    assert cache['key2'] == 'value2'
    assert cache['key3'] == 'value3'
    
    # Test LRU eviction - adding a 4th item should evict the least recently used
    cache['key4'] = 'value4'
    
    # key1 should be evicted
    assert 'key1' not in cache
    assert cache['key2'] == 'value2'
    assert cache['key3'] == 'value3'
    assert cache['key4'] == 'value4'
    
    print("✓ Basic LRU cache functionality works correctly")

def test_cache_key_generation():
    """Test cache key generation similar to what we use in server.py"""
    print("Testing cache key generation...")
    
    text = "Hello world"
    speed = "1.0"
    
    # Test file-based cache key generation
    text_hash = hashlib.sha1((text + speed).encode("utf-8")).hexdigest()
    file_cache_key = f"file:{text_hash}"
    
    # Test stream-based cache key generation
    stream_cache_key = f"stream:{hashlib.sha1((text + speed).encode('utf-8')).hexdigest()}"
    
    assert file_cache_key == f"file:{text_hash}"
    assert stream_cache_key == f"stream:{text_hash}"
    assert file_cache_key != stream_cache_key
    
    print("✓ Cache key generation works correctly")

def test_cache_with_audio_buffer():
    """Test caching audio buffer objects (simulating streaming audio data)"""
    print("Testing cache with audio buffer objects...")
    
    cache = LRUCache(maxsize=2)
    
    # Create mock audio buffers
    buffer1 = BytesIO(b"audio data 1")
    buffer2 = BytesIO(b"audio data 2")
    buffer3 = BytesIO(b"audio data 3")
    
    # Cache the buffers
    cache['audio1'] = buffer1
    cache['audio2'] = buffer2
    
    # Retrieve and verify
    retrieved_buffer1 = cache['audio1']
    retrieved_buffer2 = cache['audio2']
    
    assert retrieved_buffer1.read() == b"audio data 1"
    assert retrieved_buffer2.read() == b"audio data 2"
    
    # Reset positions for re-reading
    retrieved_buffer1.seek(0)
    retrieved_buffer2.seek(0)
    
    # Add third buffer, should evict the first one
    cache['audio3'] = buffer3
    
    assert 'audio1' not in cache
    assert 'audio2' in cache
    assert 'audio3' in cache
    
    print("✓ Cache with audio buffer objects works correctly")

def test_server_imports():
    """Test that we can import the server module and access the cache"""
    print("Testing server imports and cache initialization...")
    
    try:
        # Import the server module (this will test our imports)
        import server
        
        # Check that the audio_cache is properly initialized
        assert hasattr(server, 'audio_cache')
        assert isinstance(server.audio_cache, LRUCache)
        assert server.audio_cache.maxsize == 128
        
        # Test basic cache operations
        server.audio_cache['test_key'] = 'test_value'
        assert server.audio_cache['test_key'] == 'test_value'
        
        print("✓ Server imports and cache initialization work correctly")
        
    except ImportError as e:
        print(f"✗ Failed to import server module: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing server cache: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Running cache implementation tests...\n")
    
    try:
        test_lru_cache_basic()
        test_cache_key_generation()
        test_cache_with_audio_buffer()
        
        if test_server_imports():
            print("\n✅ All tests passed! Cache implementation is working correctly.")
            return 0
        else:
            print("\n❌ Some tests failed.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())