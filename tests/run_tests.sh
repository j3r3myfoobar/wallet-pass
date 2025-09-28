#!/bin/bash

# Install test dependencies
pip3 install -r tests/requirements.txt

# Run unit tests with coverage
echo "Running unit tests with coverage..."
python3 -m pytest tests/ -v --cov=lambda_functions --cov-report=html --cov-report=term

# Check if all tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "Coverage report generated in htmlcov/index.html"
else
    echo "❌ Some tests failed!"
    exit 1
fi