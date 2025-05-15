"""
MeditationOrchestrator module for coordinating the meditation generation workflow.
This module orchestrates the process of finding, downloading, and checking meditation audio.
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
import asyncio

from app.agents.audio_retriever import AudioRetrieverAgent
from app.agents.audio_downloader import AudioDownloaderAgent
from app.agents.audio_quality_checker import AudioQualityCheckerAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MeditationOrchestrator:
    """
    Orchestrator that coordinates the workflow between meditation generation agents.
    Manages the full process from finding meditation URLs to delivering final audio files.
    """
    
    def __init__(self, language="english", cache_dir=None):
        """
        Initialize the meditation orchestrator and its component agents.
        
        Args:
            language: Default language for meditations (english or french)
            cache_dir: Directory to cache downloaded audio files
        """
        # Set default language
        self.language = language
        
        # Set up cache directory
        if cache_dir is None:
            self.cache_dir = Path(__file__).parent.parent / "assets" / "cached_audio"
        else:
            self.cache_dir = Path(cache_dir)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize all agents
        self.retriever = AudioRetrieverAgent(cache_dir=self.cache_dir)
        self.downloader = AudioDownloaderAgent(cache_dir=self.cache_dir)
        self.quality_checker = AudioQualityCheckerAgent()
        
        # Maximum number of attempts to find a good meditation
        self.max_attempts = 5  # Increased from 3 to give more chances to find working audio
    
    async def generate_meditation(self, mood, language=None, output_path=None):
        """
        Generate a meditation based on the provided mood.
        
        This method orchestrates the full workflow:
        1. Find a meditation audio URL using the AudioRetrieverAgent
        2. Download the audio using the AudioDownloaderAgent
        3. Check the audio quality using the AudioQualityCheckerAgent
        4. Optionally trim or adjust the audio if needed
        
        Args:
            mood: The mood to base the meditation on
            language: Language preference (defaults to the instance language)
            output_path: Optional path to save the meditation
            
        Returns:
            Path to the final meditation audio file
        """
        # Use instance language if none provided
        language = language or self.language
        logger.info(f"Generating meditation for mood: {mood}, language: {language}")
        
        # Create a temporary file if no output path provided
        if not output_path:
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            output_path = temp_file.name
            temp_file.close()
        
        # Store temporary files to clean up later
        temp_files = []
        final_audio_path = None
        
        # Track previously failed URLs to avoid reusing them
        failed_urls = set()
        
        # Try multiple attempts to find a suitable meditation
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.max_attempts} to find a suitable meditation")
                
                # Step 1: Find a meditation audio URL (that hasn't failed before)
                meditation_url = None
                max_url_attempts = 3  # Maximum number of attempts to find a new URL
                for url_attempt in range(1, max_url_attempts + 1):
                    meditation_url = await self.retriever.find_meditation(mood, language)
                    if meditation_url not in failed_urls:
                        logger.info(f"Found new meditation URL: {meditation_url}")
                        break
                    logger.warning(f"URL has failed before, trying another one (attempt {url_attempt}/{max_url_attempts})")
                
                if meditation_url in failed_urls:
                    logger.warning("Couldn't find a new URL after multiple attempts, using the last one anyway")
                
                logger.info(f"Using meditation URL: {meditation_url}")
                
                # Step 2: Download the meditation audio
                audio_path = await self.downloader.download_audio(meditation_url, mood, language)
                logger.info(f"Downloaded meditation audio to: {audio_path}")
                temp_files.append(audio_path)
                
                # Check if this is a fallback audio file (which indicates download failed)
                if "fallback" in audio_path or "error" in audio_path or os.path.getsize(audio_path) < 10240:  # Less than 10KB
                    failed_urls.add(meditation_url)
                    logger.warning(f"Download failed or resulted in a small file for URL: {meditation_url}, added to failed URLs")
                    continue  # Skip quality check and try another URL
                
                # Step 3: Check audio quality
                is_acceptable, quality_details = await self.quality_checker.check_quality(audio_path)
                
                # If quality is acceptable or we're on our last attempt, use this file
                if is_acceptable or attempt == self.max_attempts:
                    logger.info(f"Audio quality acceptable: {is_acceptable}")
                    logger.info(f"Quality details: {quality_details}")
                    
                    # If the audio is too long, trim it
                    if quality_details.get("duration_minutes", 0) > 12:
                        logger.info("Audio is too long, trimming...")
                        trimmed_path = await self.quality_checker.trim_audio_if_needed(audio_path)
                        if trimmed_path != audio_path:
                            temp_files.append(trimmed_path)
                            audio_path = trimmed_path
                    
                    # Copy to output path if needed
                    if audio_path != output_path:
                        shutil.copy2(audio_path, output_path)
                    
                    final_audio_path = output_path
                    
                    if is_acceptable:
                        logger.info("Found acceptable meditation audio, stopping search")
                        break
                    else:
                        logger.warning("Using last attempt meditation despite quality issues")
                else:
                    logger.warning(f"Rejected audio due to quality issues: {quality_details.get('issues', [])}")
                    # Add URL to failed list to avoid reusing it
                    failed_urls.add(meditation_url)
                    # Continue to next attempt
            
            except Exception as e:
                logger.error(f"Error in attempt {attempt}: {str(e)}")
                # If we've identified a URL, mark it as failed
                if meditation_url:
                    failed_urls.add(meditation_url)
                # Continue to next attempt
        
        # If we couldn't find a suitable file after all attempts
        if final_audio_path is None:
            logger.warning("Failed to find a suitable meditation after all attempts")
            
            # Use the last downloaded file as a fallback if available and reasonably sized
            valid_files = []
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file) and os.path.getsize(temp_file) > 10240:  # Larger than 10KB
                        valid_files.append(temp_file)
                except Exception:
                    # Skip files that can't be checked
                    pass
                    
            if valid_files:
                last_file = valid_files[-1]
                if os.path.exists(last_file):
                    logger.info(f"Using last valid file as fallback: {last_file}")
                    if last_file != output_path:
                        shutil.copy2(last_file, output_path)
                    final_audio_path = output_path
            
            # If we still don't have a valid file, try one more time with the freemindfulness URL
            if final_audio_path is None or os.path.getsize(final_audio_path) < 10240:
                logger.warning("Attempting one last guaranteed fallback URL")
                try:
                    # Use a guaranteed working meditation URL from freemindfulness.org
                    fallback_url = "https://www.freemindfulness.org/download/Breath%20meditation.mp3"
                    audio_path = await self.downloader.download_audio(fallback_url, mood, language)
                    if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 10240:
                        if audio_path != output_path:
                            shutil.copy2(audio_path, output_path)
                        final_audio_path = output_path
                        temp_files.append(audio_path)
                except Exception as e:
                    logger.error(f"Error with final fallback: {str(e)}")
            
            # If all else fails, create a placeholder file
            if final_audio_path is None or os.path.getsize(final_audio_path) < 1024:
                logger.warning("Creating empty placeholder file")
                Path(output_path).touch()
                final_audio_path = output_path
        
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file) and temp_file != output_path:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file {temp_file}: {str(e)}")
        
        logger.info(f"Meditation generation complete: {final_audio_path}")
        return final_audio_path
    
    async def close(self):
        """
        Close all resources used by the orchestrator and its agents.
        """
        if hasattr(self.downloader, 'close'):
            await self.downloader.close() 