#!/usr/bin/env python
"""
Setup script for development environment.
Creates necessary directories and placeholder files.
"""
import os
import sys
from pathlib import Path

def setup_dev_environment():
    """Set up the development environment."""
    print("Setting up development environment...")
    
    # Add the project root to Python path
    project_root = Path(__file__).resolve().parent
    sys.path.append(str(project_root))
    
    # Import the placeholder creators
    from app.utils.create_sound_placeholders import create_sound_placeholders
    from app.utils.create_audio_placeholders import create_audio_placeholders
    
    # Create placeholder ambient sound files
    create_sound_placeholders()
    
    # Create placeholder cached audio files
    create_audio_placeholders()
    
    print("Development environment setup complete!")
    print("Run ./start.sh to start the API server")

if __name__ == "__main__":
    setup_dev_environment() 