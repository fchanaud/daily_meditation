#!/bin/bash

# Daily Meditation Application Starter
# IMPORTANT: This application requires Python 3.11.x
# It is NOT compatible with Python 3.12 or newer due to dependency constraints

# Setup variables
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
DEBUG=${DEBUG:-true}

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Current version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" != *"Python 3"* ]]; then
    echo "Warning: This application requires Python 3.11.x"
    echo "Current version: $PYTHON_VERSION"
    echo "Please create and activate a Python 3.11 virtual environment before running this script."
    echo "Attempting to continue, but may encounter errors."
elif [[ "$PYTHON_VERSION" != *"Python 3.11"* ]]; then
    echo "Warning: This application requires Python 3.11.x"
    echo "Current version: $PYTHON_VERSION"
    echo "For best results, please use Python 3.11.x"
    echo "Attempting to continue, but may encounter errors."
else
    echo "Python version is compatible."
fi

# Set up environment if needed
if [ ! -d "venv" ]; then
    echo "Virtual environment not found, creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Activate virtual environment if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Create directories if they don't exist
mkdir -p app/static/meditations
mkdir -p app/assets/cached_audio

# Clean up old meditation files (older than 12 hours)
find app/static/meditations -name "*.mp3" -type f -mmin +720 -delete

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if running in production or development
if [[ -z "${PORT}" ]]; then
  # Development mode - use uvicorn with reload
  echo "Starting development server..."
  python3 -m app.api.app
else
  # Production mode - use gunicorn
  echo "Starting production server on port ${PORT}..."
  gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT} --workers 1 --threads 8 app.api.app:app
fi 