# Daily Meditation App

A FastAPI backend that provides personalized 10-minute meditation sessions based on your current mood. The app scrapes the web for meditation audio files that match your mood and ensures they meet quality standards before delivery.

## Features

- Mood-based meditation retrieval
- Support for English and French meditations
- Web scraping to find relevant meditation audio
- Audio quality validation
- Stateless design (no user accounts or history)
- Ready for iOS Shortcuts integration

## Technical Stack

- FastAPI for the API backend
- Web scraping for meditation audio retrieval
- pydub for audio processing and quality checking
- Render for deployment

## Agentic Workflow

The app uses a modular agent system:

1. **AudioRetrieverAgent**: Scrapes the web to find meditation audio URLs matching a mood
2. **AudioDownloaderAgent**: Downloads the audio files from the provided URL
3. **AudioQualityCheckerAgent**: Validates that the audio quality meets standards (duration, bitrate, etc.)
4. **MeditationOrchestrator**: Coordinates the workflow between all agents

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
