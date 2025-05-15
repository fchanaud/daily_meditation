"""
AudioRetrieverAgent module for finding meditation audio files on the web.
This agent scrapes YouTube to find meditation audio URLs based on mood.
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
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioRetrieverAgent:
    """
    Agent for retrieving meditation audio files from YouTube based on mood.
    Scrapes YouTube to find appropriate meditation audio files.
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
        
        # Map moods to search queries for YouTube
        self.mood_to_query = {
            "calm": ["calm meditation music 10 minutes", "calming meditation guided", "peaceful meditation"],
            "focused": ["focus meditation 10 minutes", "concentration meditation", "focus meditation guided"],
            "relaxed": ["relaxing meditation 10 minutes", "relaxation guided meditation", "sleep meditation"],
            "energized": ["energizing meditation music", "morning meditation", "energy boost meditation"],
            "grateful": ["gratitude meditation 10 minutes", "gratitude practice guided", "appreciation meditation"],
            "happy": ["happiness meditation 10 minutes", "joyful meditation guided", "positive energy meditation"],
            "peaceful": ["peaceful meditation 10 minutes", "peace meditation guided", "tranquil meditation"],
            "confident": ["confidence meditation 10 minutes", "self-esteem meditation", "empowerment meditation"],
            "creative": ["creativity meditation 10 minutes", "creative flow meditation", "inspiration meditation"],
            "compassionate": ["compassion meditation 10 minutes", "loving-kindness meditation", "heart meditation"]
        }
        
        # Define YouTube search URL template
        self.youtube_search_url = "https://www.youtube.com/results?search_query="
        
        # Cache for YouTube video URLs to avoid repeatedly scraping the same pages
        self.youtube_cache_file = self.cache_dir / "youtube_cache.json"
        self.youtube_cache = self._load_youtube_cache()
        
        # UCLA Mindful URL for French meditations (keeping as a fallback)
        self.ucla_mindful_url = "https://www.uclahealth.org/uclamindful/guided-meditations"
        
        # Direct links to UCLA Mindful meditation files (French)
        self.ucla_french_meditations = [
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-bodyscan.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-breathsoundbody.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-breathing.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-complete.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-lovingKindness.mp3",
            "https://d1cy5zxxhbcbkk.cloudfront.net/guided-meditations/French-workingwithdifficulties.mp3"
        ]
        
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
    
    def _load_youtube_cache(self):
        """
        Load the YouTube URL cache from the JSON file.
        
        Returns:
            Dictionary containing cached YouTube URLs
        """
        if os.path.exists(self.youtube_cache_file):
            try:
                with open(self.youtube_cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("YouTube cache file is corrupted. Creating a new one.")
                return {}
        return {}
    
    def _save_youtube_cache(self):
        """
        Save the YouTube URL cache to the JSON file.
        """
        try:
            with open(self.youtube_cache_file, 'w') as f:
                json.dump(self.youtube_cache, f)
        except Exception as e:
            logger.error(f"Error saving YouTube cache: {str(e)}")
    
    async def find_meditation(self, mood, language="english"):
        """
        Find a meditation audio URL matching the mood from YouTube.
        
        Args:
            mood: The mood to search for
            language: Preferred language for the meditation
            
        Returns:
            Tuple of (URL of a meditation audio file, source_info dict)
            or just URL if no source info is available
        """
        # Normalize the mood
        mood = mood.lower().strip()
        language = language.lower().strip()
        
        # For French language, search YouTube using French terms
        if language == "french":
            logger.info("Looking for French meditation videos on YouTube")
            
            # Create French-specific queries for this mood
            french_queries = {
                "calm": ["méditation calme 10 minutes", "musique méditation calme", "méditation pleine conscience"],
                "focused": ["méditation concentration 10 minutes", "méditation focus", "méditation attention"],
                "relaxed": ["méditation relaxante 10 minutes", "méditation pour dormir", "relaxation guidée"],
                "energized": ["méditation énergie 10 minutes", "méditation revitalisante", "méditation matin"],
                "grateful": ["méditation gratitude 10 minutes", "méditation reconnaissance", "pratique de gratitude"],
                "happy": ["méditation bonheur 10 minutes", "méditation joie", "méditation bien-être"],
                "peaceful": ["méditation paix 10 minutes", "méditation tranquillité", "méditation sérénité"],
                "confident": ["méditation confiance 10 minutes", "méditation confiance en soi", "méditation estime de soi"],
                "creative": ["méditation créativité 10 minutes", "méditation inspiration", "méditation imagination"],
                "compassionate": ["méditation compassion 10 minutes", "méditation bienveillance", "méditation amour"]
            }
            
            # Use French-specific queries if available, otherwise use generic French meditation query
            if mood in french_queries:
                queries = french_queries[mood]
            else:
                queries = ["méditation guidée 10 minutes", "méditation pleine conscience", "méditation relaxante"]
        else:
            # Get appropriate search queries for this mood for English
            if mood in self.mood_to_query:
                queries = self.mood_to_query[mood]
            else:
                # Default queries if mood isn't in our predefined list
                queries = ["meditation music", "mindfulness meditation", "relaxing music"]
        
        # Create a cache key
        cache_key = f"{mood}_{language}"
        
        # Check if we have cached YouTube URLs for this mood and language
        if cache_key in self.youtube_cache and self.youtube_cache[cache_key]:
            logger.info(f"Using cached YouTube URLs for mood: {mood}, language: {language}")
            # Get a random entry from the cache
            selected_entry = random.choice(self.youtube_cache[cache_key])
            
            # Check if it's a URL or a dict with URL and metadata
            if isinstance(selected_entry, dict) and 'url' in selected_entry:
                url = selected_entry['url']
                # Create source info from the cached metadata
                source_info = {
                    'youtube_url': url,
                    'title': selected_entry.get('title', 'Meditation Video')
                }
                return (url, source_info)
            else:
                # Just a URL without metadata
                return selected_entry
        
        # Try YouTube search with our queries
        all_youtube_urls = []
        youtube_metadata = {}
        
        for query in queries:
            logger.info(f"Searching YouTube with query: {query}")
            youtube_urls = await self._search_youtube(query)
            if youtube_urls:
                all_youtube_urls.extend(youtube_urls)
                logger.info(f"Found {len(youtube_urls)} YouTube videos for query: {query}")
            await asyncio.sleep(0.5)
        
        # Filter URLs to match our criteria and get metadata
        filtered_entries = await self._filter_youtube_urls(all_youtube_urls)
        
        if filtered_entries:
            # Cache the results for future use
            self.youtube_cache[cache_key] = filtered_entries
            self._save_youtube_cache()
            
            # Return a random entry with its metadata
            selected_entry = random.choice(filtered_entries)
            
            if isinstance(selected_entry, dict) and 'url' in selected_entry:
                url = selected_entry['url']
                source_info = {
                    'youtube_url': url,
                    'title': selected_entry.get('title', 'Meditation Video')
                }
                logger.info(f"Found suitable YouTube meditation: {url}")
                return (url, source_info)
            else:
                # Just in case some entries don't have metadata
                logger.info(f"Found suitable YouTube meditation: {selected_entry}")
                return selected_entry
        
        # If no YouTube videos found, fall back to UCLA meditation files only for French language
        if language == "french":
            logger.warning(f"No suitable YouTube meditations found for {mood} in French. Using UCLA fallback.")
            fallback_url = random.choice(self.ucla_french_meditations)
            return (fallback_url, {'youtube_url': None, 'title': 'UCLA French Meditation'})
        
        # For other languages, try one more general search
        logger.warning(f"No suitable YouTube meditations found for {mood}. Trying generic search.")
        if language == "french":
            generic_query = "méditation guidée"
        else:
            generic_query = "guided meditation"
            
        youtube_urls = await self._search_youtube(generic_query)
        if youtube_urls:
            url = youtube_urls[0]
            source_info = {
                'youtube_url': url,
                'title': 'Meditation Video'
            }
            return (url, source_info)
            
        # Absolute last resort - return a UCLA URL for French or a default URL for other languages
        if language == "french":
            fallback_url = random.choice(self.ucla_french_meditations)
        else:
            fallback_url = "https://mindfulness-exercises-free.s3.amazonaws.com/10-Minute-Mindfulness-Meditation.mp3"
            
        return (fallback_url, {'youtube_url': None, 'title': 'Fallback Meditation'})
    
    async def _search_youtube(self, query):
        """
        Search YouTube for meditation videos matching the query.
        
        Args:
            query: Search query
            
        Returns:
            List of YouTube video URLs
        """
        try:
            # Format query for URL
            formatted_query = quote(f"{query} meditation")
            search_url = f"{self.youtube_search_url}{formatted_query}"
            
            # Choose a random user agent
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"YouTube search returned status {response.status}")
                        return []
                    
                    html = await response.text()
            
            # Parse video IDs from the response
            # YouTube search results contain a pattern like "videoId":"VIDEO_ID"
            video_ids = re.findall(r'"videoId":"([^"]+)"', html)
            
            # Create URLs from video IDs and return
            youtube_urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
            
            # Remove duplicates
            youtube_urls = list(set(youtube_urls))
            
            return youtube_urls[:10]  # Limit to first 10 results
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {str(e)}")
            return []
    
    async def _filter_youtube_urls(self, urls):
        """
        Filter YouTube URLs to find those that match our criteria.
        - Duration between 8-15 minutes
        - Has proper meditation content
        
        Args:
            urls: List of YouTube URLs to filter
            
        Returns:
            List of filtered YouTube entries (dicts with url, title, and duration)
        """
        filtered_entries = []
        
        for url in urls:
            try:
                # Get video info to check duration
                video_info = await self._get_youtube_video_info(url)
                
                if video_info is None:
                    continue
                
                # Check if duration is suitable (8-15 minutes)
                duration_seconds = video_info.get('duration_seconds', 0)
                if 480 <= duration_seconds <= 900:
                    # Store as dict with metadata
                    entry = {
                        'url': url,
                        'title': video_info.get('title', ''),
                        'duration_seconds': duration_seconds
                    }
                    filtered_entries.append(entry)
                    # Once we have 5 suitable entries, stop checking
                    if len(filtered_entries) >= 5:
                        break
                
            except Exception as e:
                logger.error(f"Error filtering YouTube URL {url}: {str(e)}")
                continue
            
            # Add a small delay to avoid rate limiting
            await asyncio.sleep(0.2)
        
        return filtered_entries
    
    async def _get_youtube_video_info(self, url):
        """
        Get information about a YouTube video, including duration.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary containing video information
        """
        try:
            # Extract video ID from URL
            video_id = re.search(r'v=([^&]+)', url).group(1)
            
            # Use YouTube's oEmbed API to get basic info
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(oembed_url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    oembed_data = await response.json()
            
            # Now get the video page to extract duration
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, headers={'User-Agent': random.choice(self.user_agents)}, timeout=15) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
            
            # Extract length from the HTML - YouTube embeds duration in a meta tag
            duration_match = re.search(r'<meta itemprop="duration" content="PT([0-9]+)M([0-9]+)S">', html)
            
            if duration_match:
                minutes = int(duration_match.group(1))
                seconds = int(duration_match.group(2))
                duration_seconds = minutes * 60 + seconds
            else:
                # Alternative method to find duration
                length_match = re.search(r'"lengthSeconds":"(\d+)"', html)
                if length_match:
                    duration_seconds = int(length_match.group(1))
                else:
                    duration_seconds = 0
            
            # Get title and other info
            title = oembed_data.get('title', '')
            
            return {
                'id': video_id,
                'title': title,
                'duration_seconds': duration_seconds,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error getting YouTube video info: {str(e)}")
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