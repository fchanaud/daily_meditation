# Daily Meditation App

A FastAPI backend that generates personalized 10-minute meditation sessions based on your current mood. The app uses LangChain agents to retrieve meditation audio from the web, and mix with ambient sounds.

## Features

- Mood-based meditation retrieval
- Support for English and French meditations
- Web scraping to find relevant meditation audio
- Ambient sound mixing
- Stateless design (no user accounts or history)
- Ready for iOS Shortcuts integration

## Technical Stack

- FastAPI for the API backend
- LangChain for agent orchestration
- Web scraping for meditation audio retrieval
- ffmpeg/pydub for audio processing
- Render for deployment

## API Usage

Send a POST request to `/generate-meditation` with a JSON payload containing your mood and preferred language:

```json
{
  "mood": "calm",
  "language": "english"
}
```

The response will be an MP3 audio file that can be played directly on your device.

## iOS Shortcuts Integration

An iOS Shortcut can be set up to:
1. Prompt for a mood selection and language preference
2. Call the API endpoint
3. Play the returned audio automatically
