# Daily Meditation App

A web application that helps users find personalized meditation audio based on their current mood.

## Features

- 🧘‍♂️ Select from 10 different mood options
- 🎵 Automatically finds meditation audio from Pixabay and Archive.org
- 🌍 Supports multiple languages (English and French)
- 🔄 Real-time progress indicators during audio retrieval
- 🎧 Integrated audio player with auto-playback

## Recent Improvements

- Added pre-vetted Pixabay URLs known to work
- Implemented rotating user agents to avoid being blocked
- Added direct Archive.org collection scraping
- Expanded the acceptable meditation duration range to 8-15 minutes
- Added better error handling and fallback mechanisms
- Improved duration detection in audio files
- Added progress indicators to show audio retrieval status
- Integrated audio player with automatic playback

## How It Works

1. User selects their current mood from 10 options
2. User chooses their preferred language
3. App searches Pixabay and Archive.org for suitable meditation audio
4. Audio is streamed directly in the browser with controls
5. Audio files are temporarily cached for better performance

## Technical Details

The application is built using:

- FastAPI for the backend API
- Jinja2 templates for server-side rendering
- Bootstrap for responsive UI design
- HTML5 audio player for meditation playback
- BeautifulSoup for web scraping

## Running the App

```bash
# Clone the repository
git clone https://github.com/yourusername/daily-meditation.git
cd daily-meditation

# Install dependencies
pip install -r requirements.txt

# Start the application
./start.sh
```

The app will be available at http://localhost:8000

## API Endpoints

- `GET /`: Home page with mood selection interface
- `POST /generate-meditation`: Generate a meditation based on mood and language
- `GET /available-moods`: Get list of available moods
- `GET /available-languages`: Get list of available languages
