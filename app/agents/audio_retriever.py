"""
AudioRetrieverAgent module for finding meditation audio files on the web.
This agent scrapes Pixabay and Archive.org to find meditation audio URLs based on mood.
"""

import os
import random
import requests
import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin, quote
from bs4 import BeautifulSoup
import re
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioRetrieverAgent:
    """
    Agent for retrieving meditation audio files from Pixabay and Archive.org based on mood.
    Scrapes these websites to find appropriate 10-minute audio files.
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize the audio retriever agent.
        
        Args:
            cache_dir: Directory to cache downloaded audio files
        """
        if cache_dir is None:
            self.cache_dir = Path(__file__).parent.parent / "assets" / "cached_audio"
        else:
            self.cache_dir = Path(cache_dir)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Map moods to search queries for each site
        self.mood_to_query = {
            "calm": ["calm meditation music 10 minutes", "calm meditation 10 min"],
            "focused": ["focus meditation music 10 minutes", "concentration meditation 10 min"],
            "relaxed": ["relaxing meditation music 10 minutes", "relaxation 10 min"],
            "energized": ["energizing meditation music 10 minutes", "energy meditation 10 min"],
            "grateful": ["gratitude meditation music 10 minutes", "gratitude meditation 10 min"],
            "happy": ["happiness meditation music 10 minutes", "joy meditation 10 min"],
            "peaceful": ["peaceful meditation music 10 minutes", "peace meditation 10 min"],
            "confident": ["confidence meditation music 10 minutes", "self-esteem meditation 10 min"],
            "creative": ["creativity meditation music 10 minutes", "creative meditation 10 min"],
            "compassionate": ["compassion meditation music 10 minutes", "loving-kindness meditation 10 min"]
        }
        
        # Define scraping URLs for each site
        self.pixabay_base_url = "https://pixabay.com/music/search/"
        self.archive_base_url = "https://archive.org/search.php?query="
        
        # User agent for requests to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    
    async def find_meditation(self, mood, language="english"):
        """
        Find a meditation audio URL matching the mood from Pixabay or Archive.org.
        
        Args:
            mood: The mood to search for
            language: Preferred language for the meditation
            
        Returns:
            URL of a meditation audio file
        """
        # Normalize the mood
        mood = mood.lower().strip()
        
        # Get appropriate search queries for this mood
        if mood in self.mood_to_query:
            queries = self.mood_to_query[mood]
        else:
            # Default queries if mood isn't in our predefined list
            queries = ["meditation music 10 minutes", "mindfulness meditation 10 min"]
        
        # Add language to the query if it's not English
        if language.lower() != "english":
            queries = [f"{q} {language}" for q in queries]
        
        # Randomly decide which source to try first
        sources = ["pixabay", "archive"]
        random.shuffle(sources)
        
        # Try each source with different queries
        for source in sources:
            for query in queries:
                logger.info(f"Searching for meditation on {source} with query: {query}")
                
                if source == "pixabay":
                    audio_url = await self._scrape_pixabay(query)
                else:  # archive.org
                    audio_url = await self._scrape_archive_org(query)
                
                if audio_url:
                    logger.info(f"Found meditation audio URL on {source}: {audio_url}")
                    return audio_url
                
                # Respect rate limits
                await asyncio.sleep(1)
        
        # If we still haven't found anything, use a fallback URL
        logger.warning("Couldn't find meditation audio, using fallback URL")
        return self._get_fallback_url(mood)
    
    async def _scrape_pixabay(self, query):
        """
        Scrape Pixabay for meditation audio.
        
        Args:
            query: Search query
            
        Returns:
            URL of a suitable meditation audio file if found, None otherwise
        """
        try:
            # Format query for URL
            formatted_query = quote(query.replace(" ", "+"))
            search_url = f"{self.pixabay_base_url}{formatted_query}/"
            
            logger.info(f"Scraping Pixabay with URL: {search_url}")
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for audio elements on Pixabay
            audio_links = []
            
            # Pixabay has audio tracks with duration information
            for audio_container in soup.select('.audio-content'):
                # Check if this is around 10 minutes
                duration_elem = audio_container.select_one('.duration')
                if duration_elem:
                    duration_text = duration_elem.text.strip()
                    # Look for durations between 8-12 minutes
                    if self._is_duration_suitable(duration_text):
                        # Find the download link in this container
                        download_btn = audio_container.select_one('a.download-button')
                        if download_btn and 'href' in download_btn.attrs:
                            href = download_btn['href']
                            # Make absolute URL if needed
                            audio_url = urljoin(search_url, href)
                            audio_links.append(audio_url)
            
            # Also search for audio players with mp3 sources
            for audio_tag in soup.find_all('audio'):
                source_tags = audio_tag.find_all('source')
                for source in source_tags:
                    if source.get('src') and (source.get('type') == 'audio/mpeg' or '.mp3' in source.get('src')):
                        audio_url = urljoin(search_url, source.get('src'))
                        audio_links.append(audio_url)
            
            # Look for script tags that might contain JSON with audio URLs
            for script in soup.find_all('script', type='application/json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'tracks' in data:
                        for track in data['tracks']:
                            if 'duration' in track and 'high_mp3' in track:
                                duration_sec = track.get('duration', 0)
                                # Check if duration is around 10 minutes (600 seconds)
                                if 480 <= duration_sec <= 720:  # 8-12 minutes
                                    audio_links.append(track['high_mp3'])
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Return a random link from the filtered links
            if audio_links:
                return random.choice(audio_links)
            
        except Exception as e:
            logger.error(f"Error scraping Pixabay: {str(e)}")
        
        return None
    
    async def _scrape_archive_org(self, query):
        """
        Scrape Archive.org for meditation audio.
        
        Args:
            query: Search query
            
        Returns:
            URL of a suitable meditation audio file if found, None otherwise
        """
        try:
            # Format query for URL
            formatted_query = quote(f"{query} AND format:(mp3) AND mediatype:(audio)")
            search_url = f"{self.archive_base_url}{formatted_query}"
            
            logger.info(f"Scraping Archive.org with URL: {search_url}")
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for search results
            results = soup.select('.item-ttl')
            
            # Process each result to find audio files
            for result in results:
                try:
                    # Get the item link
                    item_link = result.find('a')
                    if not item_link or not item_link.get('href'):
                        continue
                    
                    # Get the item page URL
                    item_url = urljoin('https://archive.org', item_link.get('href'))
                    
                    # Get the item page
                    item_response = requests.get(item_url, headers=self.headers, timeout=10)
                    item_response.raise_for_status()
                    
                    item_soup = BeautifulSoup(item_response.text, 'html.parser')
                    
                    # Look for audio download links
                    download_options = item_soup.select('.format-group')
                    mp3_links = []
                    
                    for option in download_options:
                        if 'MP3' in option.text:
                            links = option.find_all('a')
                            for link in links:
                                href = link.get('href')
                                if href and href.endswith('.mp3'):
                                    # Create full URL
                                    mp3_url = urljoin('https://archive.org', href)
                                    mp3_links.append(mp3_url)
                    
                    # If we found MP3 links, return a random one
                    if mp3_links:
                        return random.choice(mp3_links)
                    
                    # Also check for audio players with sources
                    for audio_tag in item_soup.find_all('audio'):
                        for source in audio_tag.find_all('source'):
                            src = source.get('src')
                            if src and src.endswith('.mp3'):
                                return urljoin('https://archive.org', src)
                    
                    # Respect rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error processing Archive.org item: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Archive.org: {str(e)}")
        
        return None
    
    def _is_duration_suitable(self, duration_text):
        """
        Check if a duration text (e.g. "10:30") is around 10 minutes.
        
        Args:
            duration_text: Duration text to check
            
        Returns:
            True if duration is between 8-12 minutes, False otherwise
        """
        try:
            # Parse durations like "10:30" or "9:45"
            parts = duration_text.strip().split(':')
            
            if len(parts) == 2:
                minutes = int(parts[0])
                # Consider 8-12 minutes as suitable for a "10-minute" meditation
                return 8 <= minutes <= 12
            
            if len(parts) == 3:  # Hour:Minute:Second format
                hours, minutes = int(parts[0]), int(parts[1])
                # If there are hours, it's too long
                if hours > 0:
                    return False
                # Consider 8-12 minutes as suitable
                return 8 <= minutes <= 12
                
        except (ValueError, IndexError):
            pass
            
        # For unusual formats, check if "10 min" or similar is in the text
        match = re.search(r'(\d+)\s*min', duration_text.lower())
        if match:
            minutes = int(match.group(1))
            return 8 <= minutes <= 12
            
        return False
    
    def _get_fallback_url(self, mood):
        """
        Get a fallback URL for a given mood.
        
        Args:
            mood: Mood
            
        Returns:
            Fallback URL
        """
        # Dictionary of fallback URLs from Archive.org and Pixabay
        fallback_urls = {
            "calm": "https://archive.org/download/10-minute-meditation-music/10%20Minute%20Meditation%20Music.mp3",
            "focused": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c9d339a9c4.mp3?filename=ambient-piano-amp-strings-10711.mp3",
            "relaxed": "https://archive.org/download/ambient-sleep-music-for-deep-sleep/Ambient%20Sleep%20Music%20for%20Deep%20Sleep.mp3",
            "energized": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6c29ab2.mp3?filename=morning-garden-acoustic-chill-7111.mp3",
            "peaceful": "https://archive.org/download/RelaxingMeditationMusic_201611/Relaxing%20Meditation%20Music.mp3",
            "default": "https://archive.org/download/10-minute-meditation-music/10%20Minute%20Meditation%20Music.mp3"
        }
        
        return fallback_urls.get(mood, fallback_urls["default"]) 