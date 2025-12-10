#!/bin/bash

# Script to run the test suite

echo "Running Healthcare Blockchain Tests"
echo "===================================="

cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest
pytest backend/tests/ -v --cov=backend/app --cov-report=html --cov-report=term

echo ""
echo "Test coverage report generated in htmlcov/"

