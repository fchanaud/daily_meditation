# Daily Meditation App Workflow

## Overview

The Daily Meditation App uses a multi-agent architecture to find, download, and deliver high-quality meditation audio files based on the user's mood preferences. This document outlines the workflow and responsibilities of each agent.

## Agentic Workflow

### 1. AudioRetrieverAgent

**Input:** Mood string, preferred language
**Output:** URL of a meditation audio file
**Description:** Uses web scraping to search for and locate URLs of free meditation audio files that match the user's selected mood in their preferred language.

Key features:
- Maps moods to appropriate search queries
- Targets multiple free meditation resources for scraping
- Extracts audio file URLs from meditation websites
- Filters results by language preference

### 2. AudioDownloaderAgent

**Input:** URL of a meditation audio file, mood, language
**Output:** Path to downloaded audio file
**Description:** Downloads the audio file from the provided URL and saves it to a local cache directory.

Key features:
- Creates unique filenames based on mood and language
- Handles errors gracefully
- Preserves original filenames when possible
- Creates placeholder files if downloads fail

### 3. AudioQualityCheckerAgent

**Input:** Path to downloaded audio file
**Output:** Quality assessment results (boolean + details)
**Description:** Validates that the downloaded audio meets quality standards.

Key features:
- Checks audio duration (5-15 minutes ideal)
- Verifies minimum bitrate (64kbps+)
- Ensures adequate sample rate (22kHz+)
- Detects silent/corrupted files
- Provides detailed quality metrics

### 4. MeditationOrchestrator

**Description:** Coordinates the full workflow between the agents.

Workflow steps:
1. Uses AudioRetrieverAgent to find a relevant meditation audio URL
2. Uses AudioDownloaderAgent to download the audio file
3. Uses AudioQualityCheckerAgent to validate the quality
4. Makes multiple attempts if quality checks fail
5. Returns the path to the final audio file

## API Integration

The FastAPI backend exposes endpoints that leverage this agentic workflow:

- `POST /generate-meditation`: Takes mood and language preferences, orchestrates the entire workflow, and returns the meditation audio file
- `GET /available-moods`: Returns the list of supported moods
- `GET /available-languages`: Returns the list of supported languages

## iOS Shortcut Integration

The app includes a guide for creating an iOS Shortcut that:
1. Prompts the user for their mood and language preference
2. Calls the API endpoint
3. Plays the returned meditation audio

## Benefits of This Architecture

- **Modularity**: Each agent has a single responsibility, making the system easier to maintain and extend
- **Resilience**: Multiple fallback mechanisms ensure the system can recover from failures
- **Quality Assurance**: Audio quality validation ensures users receive appropriate meditation content
- **Language Support**: Built-in support for both English and French meditations
- **Extensibility**: New agents can be added to enhance functionality (e.g., text-to-speech, recommendation engine) 