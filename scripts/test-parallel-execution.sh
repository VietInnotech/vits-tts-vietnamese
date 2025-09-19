#!/bin/bash
set -euo pipefail

# Script to test parallel execution with -n auto to verify port conflict fix
# This specifically tests the pytest -n auto parameter mentioned in the task

echo "=== Testing Parallel Execution with Port Conflict Fix ==="
echo "Starting parallel execution test at $(date)"

# Install pytest-xdist for parallel execution (if not already installed)
echo "Installing pytest-xdist for parallel execution..."
pip3 install pytest-xdist

# First, let's test the dynamic port allocation directly
echo "Testing dynamic port allocation..."
python3 test_dynamic_ports.py

# Now run integration tests with parallel execution
echo "Running integration tests with parallel execution (-n auto)..."
pytest tests/integration -n auto -v --tb=short

echo "=== Parallel Execution Test Completed ==="
echo "If no port conflicts occurred, the dynamic port allocation fix is working correctly."