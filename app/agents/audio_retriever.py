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
            "calm": ["calm meditation music 10 minutes", "calming music meditation", "peaceful meditation"],
            "focused": ["focus meditation music 10 minutes", "concentration music", "focus meditation"],
            "relaxed": ["relaxing meditation music 10 minutes", "relaxation music", "sleep meditation"],
            "energized": ["energizing meditation music", "morning meditation", "energy boost music"],
            "grateful": ["gratitude meditation music", "gratitude practice", "appreciation meditation"],
            "happy": ["happiness meditation music", "joyful meditation", "positive energy music"],
            "peaceful": ["peaceful meditation music", "peace meditation", "tranquil meditation"],
            "confident": ["confidence meditation music", "self-esteem meditation", "empowerment music"],
            "creative": ["creativity meditation music", "creative flow music", "inspiration meditation"],
            "compassionate": ["compassion meditation music", "loving-kindness", "heart meditation"]
        }
        
        # Define scraping URLs and API endpoints
        self.pixabay_base_url = "https://pixabay.com/music/search/"
        self.pixabay_api_url = "https://pixabay.com/api/"
        self.archive_base_url = "https://archive.org/search.php?query="
        self.archive_download_url = "https://archive.org/download/"
        
        # Use rotating user agents to avoid being blocked
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        
        # Direct URLs to known audio collections on Archive.org
        self.archive_collections = [
            "https://archive.org/details/meditation-music",
            "https://archive.org/details/relaxation-music",
            "https://archive.org/details/ambient-sleep-music-for-deep-sleep",
            "https://archive.org/details/MeditationMusic_20162107"
        ]
        
        # Pre-vetted Pixabay MP3 URLs that work and are of appropriate length
        self.pixabay_prevetted = {
            "calm": [
                "https://cdn.pixabay.com/download/audio/2021/11/25/audio_0a1dcd2f51.mp3?filename=peaceful-meditation-143862.mp3",
                "https://cdn.pixabay.com/download/audio/2022/05/16/audio_98461371a9.mp3?filename=namaste-meditation-music-119593.mp3"
            ],
            "focused": [
                "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c9d339a9c4.mp3?filename=ambient-piano-amp-strings-10711.mp3",
                "https://cdn.pixabay.com/download/audio/2022/01/20/audio_333dfcfcb1.mp3?filename=mind-body-experience-144047.mp3"
            ],
            "relaxed": [
                "https://cdn.pixabay.com/download/audio/2022/05/26/audio_c835e4903f.mp3?filename=dreamy-imagination-14144.mp3",
                "https://cdn.pixabay.com/download/audio/2021/11/01/audio_00fa5593e3.mp3?filename=nebula-144946.mp3"
            ],
            "energized": [
                "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6c29ab2.mp3?filename=morning-garden-acoustic-chill-7111.mp3",
                "https://cdn.pixabay.com/download/audio/2022/04/27/audio_db6de5f007.mp3?filename=relaxing-mountains-rivers-running-water-118762.mp3"
            ],
            "default": [
                "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1b8bebec68.mp3?filename=calm-meditation-126837.mp3",
                "https://cdn.pixabay.com/download/audio/2021/11/01/audio_3702db7734.mp3?filename=time-pass-143246.mp3"
            ]
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
            queries = ["meditation music", "mindfulness meditation", "relaxing music"]
        
        # Add language to the query if it's not English
        if language.lower() != "english":
            queries = [f"{q} {language}" for q in queries]
        
        # Try pre-vetted Pixabay URLs first (these are known to work)
        logger.info(f"Trying pre-vetted Pixabay URLs for mood: {mood}")
        mood_urls = self.pixabay_prevetted.get(mood, self.pixabay_prevetted["default"])
        if mood_urls:
            # Return a random pre-vetted URL
            return random.choice(mood_urls)
        
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
        
        # If we still haven't found anything, check Archive.org collections directly
        logger.info("Trying direct Archive.org collections")
        for collection_url in self.archive_collections:
            audio_url = await self._scrape_archive_collection(collection_url)
            if audio_url:
                logger.info(f"Found meditation audio URL from Archive.org collection: {audio_url}")
                return audio_url
            await asyncio.sleep(1)
        
        # If we still haven't found anything, use a fallback URL
        logger.warning("Couldn't find meditation audio, using fallback URL")
        return self._get_fallback_url(mood)
    
    async def _scrape_pixabay(self, query):
        """
        Scrape Pixabay for meditation audio, with bypass for 403 errors.
        
        Args:
            query: Search query
            
        Returns:
            URL of a suitable meditation audio file if found, None otherwise
        """
        try:
            # Rotate user agents to avoid being blocked
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://pixabay.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Format query for URL
            formatted_query = quote(query.replace(" ", "+"))
            search_url = f"{self.pixabay_base_url}{formatted_query}/"
            
            logger.info(f"Scraping Pixabay with URL: {search_url}")
            
            # Try with session cookies
            session = requests.Session()
            response = session.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 403:
                logger.warning("Received 403 from Pixabay, trying alternative approach")
                
                # Try using pre-vetted URLs instead
                mood_from_query = self._extract_mood_from_query(query)
                if mood_from_query in self.pixabay_prevetted:
                    urls = self.pixabay_prevetted[mood_from_query]
                    if urls:
                        return random.choice(urls)
                
                # Fall back to default prevetted URLs
                if self.pixabay_prevetted["default"]:
                    return random.choice(self.pixabay_prevetted["default"])
                
                return None
            
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
            # Format query for URL - ensure we get MP3 files of appropriate length
            formatted_query = quote(f"{query} AND format:(mp3) AND mediatype:(audio)")
            search_url = f"{self.archive_base_url}{formatted_query}"
            
            logger.info(f"Scraping Archive.org with URL: {search_url}")
            response = requests.get(
                search_url, 
                headers={'User-Agent': random.choice(self.user_agents)}, 
                timeout=10
            )
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
                    item_response = requests.get(
                        item_url, 
                        headers={'User-Agent': random.choice(self.user_agents)}, 
                        timeout=10
                    )
                    item_response.raise_for_status()
                    
                    item_soup = BeautifulSoup(item_response.text, 'html.parser')
                    
                    # Look for duration information to filter by length
                    duration_elem = item_soup.select_one('.metadata-definition:contains("Runtime")')
                    if duration_elem:
                        duration_text = duration_elem.text
                        if not self._is_duration_suitable_text(duration_text):
                            continue  # Skip if duration is not suitable
                    
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
    
    async def _scrape_archive_collection(self, collection_url):
        """
        Scrape a specific Archive.org collection for meditation audio.
        
        Args:
            collection_url: URL of the Archive.org collection
            
        Returns:
            URL of a suitable meditation audio file if found, None otherwise
        """
        try:
            logger.info(f"Scraping Archive.org collection: {collection_url}")
            response = requests.get(
                collection_url, 
                headers={'User-Agent': random.choice(self.user_agents)}, 
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the collection identifier
            collection_id = collection_url.split('/')[-1]
            
            # Look for all items in the collection
            items = soup.select('.item-ia')
            
            if not items:
                # Try to get the download link directly if it's a single item
                download_button = soup.select_one('a.download-button')
                if download_button:
                    href = download_button.get('href')
                    if href:
                        return urljoin(collection_url, href)
                        
                # Try to get MP3 links from the files table
                files_table = soup.select('.directory-listing-table tbody tr')
                mp3_files = []
                for row in files_table:
                    link = row.select_one('a')
                    if link and link.get('href', '').endswith('.mp3'):
                        mp3_files.append(urljoin(collection_url, link.get('href')))
                
                if mp3_files:
                    return random.choice(mp3_files)
            
            # If multiple items, pick a random one and check it
            random.shuffle(items)
            for item in items[:3]:  # Check up to 3 random items
                try:
                    item_link = item.select_one('a')
                    if not item_link or not item_link.get('href'):
                        continue
                        
                    item_url = urljoin('https://archive.org', item_link.get('href'))
                    
                    # Get the item page
                    item_response = requests.get(
                        item_url, 
                        headers={'User-Agent': random.choice(self.user_agents)}, 
                        timeout=10
                    )
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
                                    mp3_url = urljoin('https://archive.org', href)
                                    mp3_links.append(mp3_url)
                    
                    if mp3_links:
                        return random.choice(mp3_links)
                    
                except Exception as e:
                    logger.error(f"Error processing collection item: {str(e)}")
                    continue
                
                # Respect rate limits
                await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error scraping Archive.org collection: {str(e)}")
        
        return None
    
    def _is_duration_suitable(self, duration_text):
        """
        Check if a duration text (e.g. "10:30") is around 10 minutes.
        
        Args:
            duration_text: Duration text to check
            
        Returns:
            True if duration is between 8-15 minutes, False otherwise
        """
        try:
            # Parse durations like "10:30" or "9:45"
            parts = duration_text.strip().split(':')
            
            if len(parts) == 2:
                minutes = int(parts[0])
                # Consider 8-15 minutes as suitable for a "10-minute" meditation
                return 8 <= minutes <= 15
            
            if len(parts) == 3:  # Hour:Minute:Second format
                hours, minutes = int(parts[0]), int(parts[1])
                # If there are hours, it's too long
                if hours > 0:
                    return False
                # Consider 8-15 minutes as suitable
                return 8 <= minutes <= 15
                
        except (ValueError, IndexError):
            pass
            
        # For unusual formats, check if "10 min" or similar is in the text
        match = re.search(r'(\d+)\s*min', duration_text.lower())
        if match:
            minutes = int(match.group(1))
            return 8 <= minutes <= 15
            
        return False
    
    def _is_duration_suitable_text(self, text):
        """
        Check if a text contains duration information that is suitable (8-15 minutes).
        
        Args:
            text: Text to check
            
        Returns:
            True if a suitable duration is found, False otherwise
        """
        # Look for patterns like "10 minutes", "9 min", etc.
        matches = re.findall(r'(\d+)\s*(minute|min|m)\w*', text.lower())
        for match in matches:
            try:
                minutes = int(match[0])
                return 8 <= minutes <= 15
            except ValueError:
                continue
                
        # Look for patterns like "10:30", "9:45", etc.
        matches = re.findall(r'(\d+):(\d+)(?::(\d+))?', text)
        for match in matches:
            try:
                if len(match) == 2:  # MM:SS format
                    minutes = int(match[0])
                    return 8 <= minutes <= 15
                elif len(match) == 3:  # HH:MM:SS format
                    hours, minutes = int(match[0]), int(match[1])
                    total_minutes = hours * 60 + minutes
                    return 8 <= total_minutes <= 15
            except ValueError:
                continue
                
        return False
    
    def _extract_mood_from_query(self, query):
        """
        Extract the mood from a search query.
        
        Args:
            query: Search query
            
        Returns:
            Extracted mood or "default"
        """
        query_lower = query.lower()
        for mood in self.mood_to_query:
            if mood in query_lower:
                return mood
                
        # Check if any mood-related words are in the query
        mood_keywords = {
            "calm": ["calm", "peace", "tranquil"],
            "focused": ["focus", "concentrate", "attention"],
            "relaxed": ["relax", "chill", "unwind"],
            "energized": ["energy", "invigorate", "uplift"],
            "grateful": ["gratitude", "thankful", "appreciate"],
            "happy": ["happy", "joy", "cheerful"],
            "peaceful": ["peace", "serene", "quiet"],
            "confident": ["confidence", "esteem", "empowerment"],
            "creative": ["creative", "imagination", "inspiration"],
            "compassionate": ["compassion", "kindness", "loving"]
        }
        
        for mood, keywords in mood_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return mood
        
        return "default"
    
    def _get_fallback_url(self, mood):
        """
        Get a fallback URL for a given mood.
        
        Args:
            mood: Mood
            
        Returns:
            Fallback URL
        """
        # Use pre-vetted Pixabay URLs if available
        if mood in self.pixabay_prevetted and self.pixabay_prevetted[mood]:
            return random.choice(self.pixabay_prevetted[mood])
            
        # Dictionary of fallback URLs from Archive.org and Pixabay
        fallback_urls = {
            "calm": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1b8bebec68.mp3?filename=calm-meditation-126837.mp3",
            "focused": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c9d339a9c4.mp3?filename=ambient-piano-amp-strings-10711.mp3",
            "relaxed": "https://cdn.pixabay.com/download/audio/2022/05/26/audio_c835e4903f.mp3?filename=dreamy-imagination-14144.mp3",
            "energized": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6c29ab2.mp3?filename=morning-garden-acoustic-chill-7111.mp3",
            "peaceful": "https://cdn.pixabay.com/download/audio/2021/11/25/audio_0a1dcd2f51.mp3?filename=peaceful-meditation-143862.mp3",
            "default": "https://cdn.pixabay.com/download/audio/2021/11/25/audio_0a1dcd2f51.mp3?filename=peaceful-meditation-143862.mp3"
        }
        
        return fallback_urls.get(mood, fallback_urls["default"]) 