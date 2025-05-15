"""
OpenAI Meditation Agent module for finding meditation videos on YouTube using OpenAI.
This agent uses OpenAI to find meditation YouTube URLs based on mood.
"""

import os
import logging
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from app.utils.config import OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenAIMeditationAgent:
    """
    Agent for finding YouTube meditation videos using OpenAI.
    Uses OpenAI to get YouTube URLs for meditation videos matching a specific mood.
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize the OpenAI meditation agent.
        
        Args:
            cache_dir: Directory to cache responses
        """
        # Store OpenAI API key
        self.api_key = OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        # Set up cache directory
        if cache_dir is None:
            self.cache_dir = Path(__file__).parent.parent / "assets" / "cached_responses"
        else:
            self.cache_dir = Path(cache_dir)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache file for OpenAI responses
        self.cache_file = self.cache_dir / "openai_meditation_cache.json"
        self.response_cache = self._load_cache()
        
        # Optimize language templates for token efficiency
        self.prompt_template = "Find YouTube meditation video: {duration} minutes, {mood} mood, {language} language. URL only."
    
    def _load_cache(self) -> Dict:
        """
        Load cached responses from file.
        
        Returns:
            Dictionary containing cached responses
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache: {str(e)}")
        return {}
    
    def _save_cache(self) -> None:
        """
        Save cached responses to file.
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.response_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
    
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
        
        # Create cache key
        cache_key = f"{mood}_{language}"
        
        # Check if we have a cached response
        if cache_key in self.response_cache:
            logger.info(f"Using cached response for mood: {mood}, language: {language}")
            cached_data = self.response_cache[cache_key]
            return cached_data["youtube_url"], {
                "youtube_url": cached_data["youtube_url"],
                "title": cached_data.get("title", "Meditation Video")
            }
        
        # Create minimal prompt based on mood and language
        prompt = self.prompt_template.format(
            duration="8-15",
            mood=mood,
            language=language
        )
        
        logger.info(f"Generating OpenAI prompt for mood: {mood}, language: {language}")
        
        try:
            # Call OpenAI API
            response = await self._call_openai(prompt)
            
            # Parse the response to extract the YouTube URL
            youtube_url = self._extract_youtube_url(response)
            
            if youtube_url:
                # Cache the response with minimal data
                cache_data = {
                    "youtube_url": youtube_url,
                    "title": f"{mood.capitalize()} Meditation"
                }
                self.response_cache[cache_key] = cache_data
                self._save_cache()
                
                logger.info(f"Found YouTube meditation: {youtube_url}")
                
                # Return URL and minimal source info
                return youtube_url, {
                    "youtube_url": youtube_url,
                    "title": f"{mood.capitalize()} Meditation"
                }
            else:
                logger.warning(f"OpenAI response did not contain a valid YouTube URL")
                # Return fallback URL
                return "https://www.youtube.com/watch?v=O-6f5wQXSu8", {
                    "youtube_url": "https://www.youtube.com/watch?v=O-6f5wQXSu8",
                    "title": "Fallback Meditation Video"
                }
                
        except Exception as e:
            logger.error(f"Error generating meditation URL with OpenAI: {str(e)}")
            # Return fallback URL
            return "https://www.youtube.com/watch?v=O-6f5wQXSu8", {
                "youtube_url": "https://www.youtube.com/watch?v=O-6f5wQXSu8",
                "title": "Fallback Meditation Video"
            }
    
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
                return "https://www.youtube.com/watch?v=O-6f5wQXSu8"
            
            # Create minimal request payload
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "Return only a YouTube URL for meditation videos (8-15 min). No other text."},
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
            # Return a fallback URL directly
            return "https://www.youtube.com/watch?v=O-6f5wQXSu8"
    
    def _extract_youtube_url(self, response_text: str) -> str:
        """
        Extract a YouTube URL from the response text.
        
        Args:
            response_text: The OpenAI response text
            
        Returns:
            The YouTube URL or empty string if not found
        """
        # Try to directly use the response if it looks like a URL
        if response_text.startswith("http") and ("youtube.com" in response_text or "youtu.be" in response_text):
            return response_text.strip()
        
        # Try to extract with regex
        import re
        url_match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+)', response_text)
        
        if url_match:
            return url_match.group(1)
        
        # If JSON was returned, try to parse it
        try:
            # Check if the text might be JSON
            if '{' in response_text and '}' in response_text:
                data = json.loads(response_text)
                if "youtube_url" in data and ("youtube.com" in data["youtube_url"] or "youtu.be" in data["youtube_url"]):
                    return data["youtube_url"]
                elif "url" in data and ("youtube.com" in data["url"] or "youtu.be" in data["url"]):
                    return data["url"]
        except:
            pass
        
        return ""

    def _parse_openai_response(self, response_text: str) -> Dict:
        """
        Parse the OpenAI response to extract the YouTube URL and title.
        
        Args:
            response_text: The OpenAI response text
            
        Returns:
            Dictionary containing the YouTube URL and title
        """
        url = self._extract_youtube_url(response_text)
        
        if url:
            return {
                "youtube_url": url,
                "title": "Meditation Video"
            }
        
        return {}
            
    async def process_feedback(self, feedback: Dict, video_data: Dict) -> None:
        """
        Process feedback from a user about a meditation video.
        This can be used to improve future recommendations.
        
        Args:
            feedback: The user's feedback responses
            video_data: Data about the video that was shown
        """
        # TODO: Implement feedback processing logic
        # This method could store feedback and use it to guide future OpenAI prompts
        pass 