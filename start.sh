#!/bin/bash

# Daily Meditation Application Starter
# IMPORTANT: This application requires Python 3.11.x
# It is NOT compatible with Python 3.12 or newer due to dependency constraints

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
if [[ $PYTHON_VERSION != *"3.11"* ]]; then
  echo "Warning: This application requires Python 3.11.x"
  echo "Current version: $PYTHON_VERSION"
  echo "Please create and activate a Python 3.11 virtual environment before running this script."
  
  # Try to find Python 3.11
  if command -v python3.11 &>/dev/null; then
    echo "Found Python 3.11, using it instead."
    PYTHON_CMD="python3.11"
  else
    echo "Attempting to continue, but may encounter errors."
    PYTHON_CMD="python"
  fi
else
  PYTHON_CMD="python"
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
  $PYTHON_CMD main.py
else
  # Production mode - use gunicorn
  echo "Starting production server on port ${PORT}..."
  gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT} --workers 1 --threads 8 app.api.app:app
fi 