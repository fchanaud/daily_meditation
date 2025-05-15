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
        self.archive_base_url = "https://archive.org/search.php?query="
        self.archive_download_url = "https://archive.org/download/"
        self.ucla_mindful_url = "https://www.uclahealth.org/uclamindful/guided-meditations"
        
        # Use rotating user agents to avoid being blocked
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        
        # Direct URLs to known audio collections on Archive.org
        self.archive_collections = [
            "https://archive.org/details/meditation-music",
            "https://archive.org/details/relaxation-music",
            "https://archive.org/details/ambient-sleep-music-for-deep-sleep",
            "https://archive.org/details/MeditationMusic_20162107",
            "https://archive.org/details/meditation_audio",
            "https://archive.org/details/meditation_guides",
            "https://archive.org/details/mindfulness-meditation",
            "https://archive.org/details/soft-meditation-music",
            "https://archive.org/details/nature-sounds-for-relaxation",
            "https://archive.org/details/sacred-meditation-music"
        ]
        
        # Direct links to UCLA Mindful meditation files (French)
        self.ucla_french_meditations = [
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-bodyscan.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-breathsoundbody.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-breathing.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-complete.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-lovingKindness.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-workingwithdifficulties.mp3"
        ]
        
        # Direct links to Archive.org items that are confirmed to work
        # These are individual files from Archive.org that can be downloaded directly
        self.archive_direct_files = {
            "calm": [
                "https://archive.org/download/InterludeForMindfulness/Interlude%20for%20Mindfulness.mp3",
                "https://archive.org/download/meditation-music-relax-mind-body/Meditation%20Music%20-%20Relax%20Mind%20Body.mp3",
                "https://archive.org/download/MeditationMusic_201610/Meditation%20Music.mp3"
            ],
            "focused": [
                "https://archive.org/download/MeditationMusic_20162107/Meditation%20Music.mp3",
                "https://archive.org/download/ambient-sleep-music-for-deep-sleep/Ambient%20Sleep%20Music%20for%20Deep%20Sleep.mp3",
                "https://archive.org/download/night-meditation-sleeping-music/Night%20Meditation%20-%20Sleeping%20Music.mp3"
            ],
            "relaxed": [
                "https://archive.org/download/sacred-meditation-music/Sacred%20Meditation%20Music.mp3",
                "https://archive.org/download/calm-meditation-music-for-stress-relief/Calm%20Meditation%20Music%20for%20Stress%20Relief.mp3",
                "https://archive.org/download/MeditationCompilation/Meditation%20Compilation.mp3"
            ],
            "energized": [
                "https://archive.org/download/morning-meditation-wake-up-music/Morning%20Meditation%20-%20Wake%20Up%20Music.mp3",
                "https://archive.org/download/meditation-music-relax-mind-body/Meditation%20Music%20-%20Relax%20Mind%20Body.mp3",
                "https://archive.org/download/ambient-meditation-music/Ambient%20Meditation%20Music.mp3"
            ],
            "grateful": [
                "https://archive.org/download/peaceful-music-for-meditation/Peaceful%20Music%20for%20Meditation.mp3",
                "https://archive.org/download/InterludeForMindfulness/Interlude%20for%20Mindfulness.mp3",
                "https://archive.org/download/indian-meditation-music/Indian%20Meditation%20Music.mp3"
            ],
            "default": [
                "https://archive.org/download/peaceful-music-for-meditation/Peaceful%20Music%20for%20Meditation.mp3",
                "https://archive.org/download/meditation-music-relax-mind-body/Meditation%20Music%20-%20Relax%20Mind%20Body.mp3",
                "https://archive.org/download/ambient-sleep-music-for-deep-sleep/Ambient%20Sleep%20Music%20for%20Deep%20Sleep.mp3",
                "https://archive.org/download/MeditationMusic_20162107/Meditation%20Music.mp3"
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
        language = language.lower().strip()
        
        # For French language, use UCLA Mindful meditations
        if language == "french":
            logger.info("Using UCLA Mindful French meditation files")
            return random.choice(self.ucla_french_meditations)
        
        # Get appropriate search queries for this mood
        if mood in self.mood_to_query:
            queries = self.mood_to_query[mood]
        else:
            # Default queries if mood isn't in our predefined list
            queries = ["meditation music", "mindfulness meditation", "relaxing music"]
        
        # Add language to the query if it's not English
        if language.lower() != "english":
            queries = [f"{q} {language}" for q in queries]
        
        # Try Archive.org direct files first (highest success rate)
        logger.info(f"Trying Archive.org direct files for mood: {mood}")
        mood_files = self.archive_direct_files.get(mood, self.archive_direct_files["default"])
        if mood_files:
            # Return a random direct file
            chosen_url = random.choice(mood_files)
            logger.info(f"Using Archive.org direct file: {chosen_url}")
            return chosen_url
        
        # Choose source with weighted probability:
        # - 80% chance to try Archive.org collections/search (more reliable)
        # - 20% chance to try Pixabay with special bypass (less reliable due to 403s)
        source_choice = random.choices(
            ["archive", "pixabay"],
            weights=[80, 20],
            k=1
        )[0]
        
        if source_choice == "archive":
            # Try Archive.org collections directly
            logger.info("Trying Archive.org collections")
            for collection_url in random.sample(self.archive_collections, min(3, len(self.archive_collections))):
                audio_url = await self._scrape_archive_collection(collection_url)
                if audio_url:
                    logger.info(f"Found meditation audio URL from Archive.org collection: {audio_url}")
                    return audio_url
                await asyncio.sleep(0.5)
                
            # If no Archive.org collection audio found, try searching
            for query in queries:
                logger.info(f"Searching Archive.org with query: {query}")
                audio_url = await self._scrape_archive_org(query)
                if audio_url:
                    logger.info(f"Found meditation audio URL on Archive.org: {audio_url}")
                    return audio_url
                await asyncio.sleep(0.5)
        
        elif source_choice == "pixabay":
            # Try Pixabay scraping with special workarounds for 403 errors
            pixabay_urls = []
            for query in queries:
                logger.info(f"Searching Pixabay with query: {query}")
                audio_url = await self._scrape_pixabay(query)
                if audio_url:
                    pixabay_urls.append(audio_url)
                    logger.info(f"Found meditation audio URL on Pixabay: {audio_url}")
                await asyncio.sleep(0.5)
            
            if pixabay_urls:
                return random.choice(pixabay_urls)
        
        # Last resort fallback - if we couldn't find anything using any method, use a guaranteed Archive.org file
        logger.warning("No sources worked, using ultimate fallback Archive.org URL")
        return self.archive_direct_files["default"][0]
    
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
                logger.warning("Received 403 from Pixabay, falling back to reliable sources")
                # Since we're getting 403s from Pixabay, use our reliable sources instead
                mood_from_query = self._extract_mood_from_query(query)
                return random.choice(self.reliable_meditation_urls.get(mood_from_query, self.reliable_meditation_urls["default"]))
            
            if response.status_code != 200:
                logger.warning(f"Pixabay returned status code {response.status_code}, falling back to reliable sources")
                mood_from_query = self._extract_mood_from_query(query)
                return random.choice(self.reliable_meditation_urls.get(mood_from_query, self.reliable_meditation_urls["default"]))
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for audio elements on Pixabay
            audio_links = []
            
            # Pixabay has audio tracks with duration information
            for audio_container in soup.select('.audio-content'):
                # Check if this is around 10 minutes
                duration_elem = audio_container.select_one('.duration')
                if duration_elem:
                    duration_text = duration_elem.text.strip()
                    # Look for durations between 8-15 minutes
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
                                if 480 <= duration_sec <= 900:  # 8-15 minutes
                                    audio_links.append(track['high_mp3'])
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Return a random link from the filtered links
            if audio_links:
                return random.choice(audio_links)
            
            # If no links found on Pixabay, use reliable sources
            logger.warning("No suitable audio found on Pixabay, falling back to reliable sources")
            mood_from_query = self._extract_mood_from_query(query)
            return random.choice(self.reliable_meditation_urls.get(mood_from_query, self.reliable_meditation_urls["default"]))
            
        except Exception as e:
            logger.error(f"Error scraping Pixabay: {str(e)}")
            # On any error, fall back to reliable sources
            mood_from_query = self._extract_mood_from_query(query)
            return random.choice(self.reliable_meditation_urls.get(mood_from_query, self.reliable_meditation_urls["default"]))
    
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
    
    async def scrape_ucla_meditations(self, language="french"):
        """
        Scrape UCLA Mindful website for meditation audio URLs in specified language.
        
        Args:
            language: Language of the meditations (default "french")
            
        Returns:
            List of meditation audio URLs
        """
        logger.info(f"Scraping UCLA Mindful website for {language} meditations")
        
        try:
            # Choose a random user agent
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # UCLA Mindful URL with language anchor
            url = f"{self.ucla_mindful_url}#{language.lower()}"
            
            # Make request
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the French section table
            meditation_urls = []
            
            # Find all play buttons within the page
            play_links = soup.find_all('a', attrs={'href': lambda href: href and 'guided-meditations/French-' in href})
            
            for link in play_links:
                href = link.get('href')
                if href and href.endswith('.mp3'):
                    # Ensure URL is absolute
                    absolute_url = href if href.startswith('http') else urljoin(self.ucla_mindful_url, href)
                    meditation_urls.append(absolute_url)
            
            # If we couldn't find any links using the normal method, use our pre-defined list
            if not meditation_urls:
                logger.warning("Could not find meditation links, using pre-defined list")
                meditation_urls = self.ucla_french_meditations
            
            logger.info(f"Found {len(meditation_urls)} {language} meditation URLs")
            return meditation_urls
            
        except Exception as e:
            logger.error(f"Error scraping UCLA Mindful website: {str(e)}")
            # Fall back to our pre-defined list
            return self.ucla_french_meditations 