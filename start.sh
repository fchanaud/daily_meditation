#!/bin/bash

# Check if the Python virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting Daily Meditation API server..."
uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload 