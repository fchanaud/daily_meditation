#!/bin/bash

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
  python main.py
else
  # Production mode - use gunicorn
  echo "Starting production server on port ${PORT}..."
  gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT} --workers 1 --threads 8 app.api.app:app
fi 