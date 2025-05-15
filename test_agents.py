#!/usr/bin/env python
"""
Test script for the meditation agents workflow.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Import the agents
from app.agents.audio_retriever import AudioRetrieverAgent
from app.agents.audio_downloader import AudioDownloaderAgent
from app.agents.audio_quality_checker import AudioQualityCheckerAgent
from app.agents.orchestrator import MeditationOrchestrator

async def test_audio_retriever():
    """Test the AudioRetrieverAgent."""
    print("\n=== Testing AudioRetrieverAgent ===")
    agent = AudioRetrieverAgent()
    
    moods = ["calm", "focused", "energized"]
    languages = ["english", "french"]
    
    for mood in moods:
        for language in languages:
            print(f"\nRetrieving {language} meditation URL for mood: {mood}")
            audio_url = await agent.retrieve(mood, preferred_language=language)
            print(f"URL: {audio_url}")
            
    return True

async def test_audio_downloader():
    """Test the AudioDownloaderAgent."""
    print("\n=== Testing AudioDownloaderAgent ===")
    retriever = AudioRetrieverAgent()
    downloader = AudioDownloaderAgent()
    
    # Test with a known URL
    test_url = "https://www.freemindfulness.org/FreeMindfulness3MinuteBreathing.mp3"
    print(f"\nDownloading test URL: {test_url}")
    download_path = await downloader.download(test_url, mood="test", language="english")
    print(f"Downloaded to: {download_path}")
    
    # Test with a URL from the retriever
    mood = "peaceful"
    language = "english"
    print(f"\nRetrieving and downloading {language} meditation for mood: {mood}")
    audio_url = await retriever.retrieve(mood, preferred_language=language)
    download_path = await downloader.download(audio_url, mood=mood, language=language)
    print(f"Downloaded to: {download_path}")
    
    return True

async def test_quality_checker():
    """Test the AudioQualityCheckerAgent."""
    print("\n=== Testing AudioQualityCheckerAgent ===")
    retriever = AudioRetrieverAgent()
    downloader = AudioDownloaderAgent()
    quality_checker = AudioQualityCheckerAgent()
    
    # Test with a known URL
    test_url = "https://www.freemindfulness.org/FreeMindfulness3MinuteBreathing.mp3"
    print(f"\nDownloading and checking test URL: {test_url}")
    download_path = await downloader.download(test_url, mood="test", language="english")
    quality_result = await quality_checker.check_quality(download_path)
    
    print(f"Quality result: {'Acceptable' if quality_result['is_acceptable'] else 'Not acceptable'}")
    if quality_result["issues"]:
        print("Issues:")
        for issue in quality_result["issues"]:
            print(f"  - {issue}")
    print("Details:")
    for key, value in quality_result["details"].items():
        print(f"  - {key}: {value}")
    
    return True

async def test_orchestrator():
    """Test the full MeditationOrchestrator workflow."""
    print("\n=== Testing MeditationOrchestrator ===")
    orchestrator = MeditationOrchestrator()
    
    moods = ["calm", "focused"]
    languages = ["english"]
    
    for mood in moods:
        for language in languages:
            print(f"\nGenerating {language} meditation for mood: {mood}")
            output_path = f"test_meditation_{mood}_{language}.mp3"
            
            # Generate the meditation
            meditation_path = await orchestrator.generate_meditation(
                mood=mood,
                language=language,
                output_path=output_path
            )
            
            print(f"Meditation saved to: {meditation_path}")
            print(f"File exists: {os.path.exists(meditation_path)}")
            print(f"File size: {os.path.getsize(meditation_path)} bytes")
    
    return True

async def main():
    """Run all the tests."""
    tests = [
        test_audio_retriever,
        test_audio_downloader,
        test_quality_checker,
        test_orchestrator
    ]
    
    # Create assets directories if they don't exist
    os.makedirs("app/assets/cached_audio", exist_ok=True)
    
    for test_func in tests:
        try:
            result = await test_func()
            if result:
                print(f"\n✅ {test_func.__name__} passed!")
            else:
                print(f"\n❌ {test_func.__name__} failed!")
        except Exception as e:
            print(f"\n❌ {test_func.__name__} failed with error: {str(e)}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 