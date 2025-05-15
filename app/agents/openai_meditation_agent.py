"""
OpenAI Meditation Agent module for finding meditation videos on YouTube using OpenAI.
This agent uses OpenAI to find meditation YouTube URLs based on mood.
"""

import os
import logging
import json
import requests
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from app.utils.config import OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import pytube for YouTube validation
try:
    from pytube import YouTube
    from pytube.exceptions import PytubeError, VideoUnavailable, RegexMatchError
    PYTUBE_AVAILABLE = True
except ImportError:
    logger.warning("pytube library not available - video validation will be limited")
    PYTUBE_AVAILABLE = False

class OpenAIMeditationAgent:
    """
    Agent for finding YouTube meditation videos using OpenAI.
    Uses OpenAI to get YouTube URLs for meditation videos matching a specific mood.
    """
    
    def __init__(self):
        """
        Initialize the OpenAI meditation agent.
        """
        # Store OpenAI API key
        self.api_key = OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        # Optimize language templates for token efficiency
        self.prompt_template = "Find YouTube meditation video: {duration} minutes, {mood} mood, {language} language. Return JSON with format: {{url: 'youtube_url_here'}}"
        
        # Maximum number of attempts to find valid video
        self.max_validation_attempts = 3
        
        # Fallback videos known to be reliable
        self.fallback_videos = [
            "https://www.youtube.com/watch?v=ZToicYcHIOU",  # 10 min meditation
            "https://www.youtube.com/watch?v=O-6f5wQXSu8",  # Generic meditation
            "https://www.youtube.com/watch?v=86m4RC_ADEY",  # Relaxing music
            "https://www.youtube.com/watch?v=1ZYbU82GVz4"   # Calm meditation
        ]
    
    async def find_meditation(self, mood: str, language: str = "english") -> Tuple[str, Dict]:
        """
        Find a meditation video URL matching the mood using OpenAI.
        
        Args:
            mood: The mood to search for
            language: Preferred language for the meditation
            
        Returns:
            Tuple of (URL of a meditation video, source_info dict)
        """
        # Normalize inputs
        mood = mood.lower().strip()
        language = language.lower().strip()
        
        # Create minimal prompt based on mood and language
        prompt = self.prompt_template.format(
            duration="8-15",
            mood=mood,
            language=language
        )
        
        logger.info(f"Generating OpenAI prompt for mood: {mood}, language: {language}")
        
        # Track validation attempts
        attempts = 0
        max_attempts = self.max_validation_attempts
        
        while attempts < max_attempts:
            attempts += 1
            try:
                # Call OpenAI API
                response = await self._call_openai(prompt)
                
                # Parse the response to extract the YouTube URL
                youtube_url = self._extract_youtube_url(response)
                
                if youtube_url:
                    logger.info(f"Found YouTube meditation: {youtube_url}")
                    
                    # Validate the YouTube URL
                    is_valid = await self._validate_youtube_url(youtube_url)
                    
                    if is_valid:
                        logger.info(f"YouTube video is valid and available: {youtube_url}")
                        
                        # Return URL and minimal source info
                        return youtube_url, {
                            "youtube_url": youtube_url,
                            "title": f"{mood.capitalize()} Meditation"
                        }
                    else:
                        logger.warning(f"YouTube video is unavailable: {youtube_url} (attempt {attempts}/{max_attempts})")
                        # Add information to prompt to avoid returning the same invalid URL
                        prompt += f" Do not return {youtube_url} as it's unavailable."
                        
                        # Short delay before trying again
                        await asyncio.sleep(0.5)
                        continue
                else:
                    logger.warning(f"OpenAI response did not contain a valid YouTube URL (attempt {attempts}/{max_attempts})")
                    
            except Exception as e:
                logger.error(f"Error generating meditation URL with OpenAI: {str(e)} (attempt {attempts}/{max_attempts})")
                
            # If we reach here, there was an issue - increase backoff slightly
            await asyncio.sleep(1)
                
        # If we've exhausted all attempts, return a fallback URL
        fallback_url = self._get_fallback_url()
        logger.warning(f"Exhausted all validation attempts, using fallback URL: {fallback_url}")
        
        return fallback_url, {
            "youtube_url": fallback_url,
            "title": "Fallback Meditation Video"
        }
    
    async def _validate_youtube_url(self, youtube_url: str) -> bool:
        """
        Validate if a YouTube URL points to an available video.
        
        Args:
            youtube_url: The YouTube URL to validate
            
        Returns:
            Boolean indicating if the URL is valid and video is available
        """
        if not youtube_url:
            return False
            
        # First check simple URL format validation
        if not ("youtube.com/watch?v=" in youtube_url or "youtu.be/" in youtube_url):
            logger.warning(f"Invalid YouTube URL format: {youtube_url}")
            return False
        
        # Fallback: Basic URL check with requests
        try:
            # Simple availability check using requests
            # Just check if the page exists, not if video is playable
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.head(youtube_url, headers=headers, timeout=5)
            
            # HEAD request worked
            if response.status_code == 200:
                # Do a more thorough check if pytube is available
                if PYTUBE_AVAILABLE:
                    try:
                        # Extract video ID from the URL
                        video_id = None
                        if "youtube.com/watch?v=" in youtube_url:
                            video_id = youtube_url.split("youtube.com/watch?v=")[1].split("&")[0]
                        elif "youtu.be/" in youtube_url:
                            video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
                            
                        # Create a YouTube object and check availability
                        yt = YouTube(youtube_url)
                        
                        # This will raise an exception if the video is unavailable
                        try:
                            # Attempt to access video metadata
                            yt.check_availability()
                            return True
                        except (PytubeError, VideoUnavailable, RegexMatchError) as e:
                            logger.warning(f"YouTube validation failed: {str(e)}")
                            return False
                    except Exception as e:
                        # If pytube fails, trust the HEAD request result
                        logger.warning(f"Pytube error, falling back to HTTP status: {str(e)}")
                        return True
                
                # If pytube isn't available, trust the HEAD request
                return True
            
            # HEAD request failed
            return False
        except Exception as e:
            logger.error(f"Error checking YouTube URL: {str(e)}")
            return False
    
    def _get_fallback_url(self) -> str:
        """
        Get a fallback YouTube URL from the list of known good videos.
        
        Returns:
            A fallback YouTube URL
        """
        import random
        return random.choice(self.fallback_videos)
    
    async def _call_openai(self, prompt: str) -> str:
        """
        Call OpenAI API with the given prompt.
        
        Args:
            prompt: The prompt to send to OpenAI
            
        Returns:
            The OpenAI response text
        """
        try:
            logger.info("Calling OpenAI API")
            
            # Check if API key is available
            if not self.api_key:
                logger.warning("No OpenAI API key found. Returning fake response.")
                return '{"url": "https://www.youtube.com/watch?v=ZToicYcHIOU"}'
            
            # Create minimal request payload
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "Return only a JSON object with a YouTube URL for meditation videos (8-15 min) in the format: {url: 'youtube_url_here'}. No other text."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 60,
                "temperature": 0.7
            }
            
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Make the API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            # Check for successful response
            if response.status_code == 200:
                response_data = response.json()
                response_text = response_data['choices'][0]['message']['content'].strip()
                logger.info(f"OpenAI response: {response_text}")
                return response_text
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            # Return a fallback URL directly as JSON
            return '{"url": "https://www.youtube.com/watch?v=ZToicYcHIOU"}'
    
    def _extract_youtube_url(self, response_text: str) -> str:
        """
        Extract a YouTube URL from the response text.
        
        Args:
            response_text: The OpenAI response text
            
        Returns:
            The YouTube URL or empty string if not found
        """
        # Try to parse JSON response
        try:
            # Handle both formats: {"url": "..."} and {url: '...'}
            if "{url:" in response_text or "{\"url\":" in response_text:
                import re
                # Extract URL directly using regex to handle inconsistent quotes
                url_match = re.search(r'(?:url:|"url":)\s*[\'"]?(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+)[\'"]?', response_text)
                if url_match:
                    return url_match.group(1)
            
            # Standard JSON parsing
            data = json.loads(response_text)
            if "url" in data and ("youtube.com" in data["url"] or "youtu.be" in data["url"]):
                return data["url"]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from response: {response_text}")
            
        # Try to extract with regex if JSON parsing failed
        import re
        url_match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+)', response_text)
        
        if url_match:
            return url_match.group(1)
        
        return ""
            
    async def process_feedback(self, feedback: Dict, video_data: Dict) -> None:
        """
        Process feedback from a user about a meditation video.
        This can be used to improve future recommendations.
        
        Args:
            feedback: The user's feedback responses
            video_data: Data about the video that was shown
        """
        # TODO: Implement feedback processing logic
        pass 