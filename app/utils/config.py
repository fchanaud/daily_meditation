import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.parent

# Load environment variables from .env file if it exists
load_dotenv(ROOT_DIR / ".env")

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# LLM API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Path configuration
ASSETS_DIR = ROOT_DIR / "app" / "assets"
AMBIENT_SOUNDS_DIR = ASSETS_DIR / "ambient_sounds"

# Ensure that the assets directories exist
os.makedirs(AMBIENT_SOUNDS_DIR, exist_ok=True)

# TTS configuration
TTS_VOICE_MODEL = os.getenv("TTS_VOICE_MODEL", "en_US-lessac-medium")

# Feature flags
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t") 