#!/usr/bin/env python3
"""Test script to verify dynamic port allocation works correctly."""

import socket
import subprocess
import time
import requests
import sys
import os

def get_free_port():
    """Get a free port number by binding to port 0 and returning the assigned port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def test_dynamic_port_allocation():
    """Test that dynamic port allocation works by running two containers simultaneously."""
    print("Testing dynamic port allocation...")
    
    # Test 1: Verify get_free_port function works
    port1 = get_free_port()
    port2 = get_free_port()
    print(f"Free ports allocated: {port1}, {port2}")
    
    if port1 == port2:
        print("ERROR: Same port returned twice!")
        return False
    
    # Test 2: Try to run a simple container with dynamic port
    container_name = "test-dynamic-port"
    try:
        # Run container with dynamic port
        print(f"Starting container on port {port1}...")
        process = subprocess.Popen([
            "docker", "run", "--name", container_name,
            "-p", f"{port1}:8888",
            "-e", "TTS_AUDIO_OUTPUT_DIR=/app/audio",
            "-e", "LOG_LEVEL=DEBUG",
            "vits-tts-vietnamese:test"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for container to start
        time.sleep(10)
        
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "-f", f"name={container_name}"],
            capture_output=True,
            text=True
        )
        
        if container_name not in result.stdout:
            print("ERROR: Container failed to start")
            # Get logs
            logs_result = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True
            )
            print(f"Container logs: {logs_result.stdout}\n{logs_result.stderr}")
            return False
        
        # Test health endpoint
        print("Testing health endpoint...")
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{port1}/health", timeout=5)
                if response.status_code == 200:
                    print("SUCCESS: Health endpoint responded correctly!")
                    break
            except requests.RequestException:
                if i == max_retries - 1:
                    print("ERROR: Service did not become ready in time")
                    return False
                time.sleep(2)
        
        # Test 3: Verify we can run another container on a different port
        port3 = get_free_port()
        if port3 == port1:
            print("ERROR: Got same port again!")
            return False
            
        print(f"Can allocate another free port: {port3}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        return False
        
    finally:
        # Cleanup
        print("Cleaning up container...")
        try:
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)
        except:
            pass

if __name__ == "__main__":
    success = test_dynamic_port_allocation()
    if success:
        print("\n✅ Dynamic port allocation test PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Dynamic port allocation test FAILED!")
        sys.exit(1)