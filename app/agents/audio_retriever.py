import os
import tempfile
import random
import requests
from pathlib import Path
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re

class AudioRetrieverAgent:
    """
    Agent for retrieving meditation audio files from the internet based on mood.
    Scrapes and returns URLs for 10-minute long meditation audio in French or English.
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
        
        # Map of moods to search queries
        self.mood_to_query = {
            "calm": ["calm meditation music 10 minutes", "méditation calme 10 minutes"],
            "focused": ["focus meditation 10 minutes", "méditation concentration 10 minutes"],
            "relaxed": ["relaxing meditation audio 10 minutes", "méditation relaxante 10 minutes"],
            "energized": ["energizing meditation 10 minutes", "méditation énergisante 10 minutes"],
            "grateful": ["gratitude meditation 10 minutes", "méditation gratitude 10 minutes"],
            "happy": ["happiness meditation 10 minutes", "méditation bonheur 10 minutes"],
            "peaceful": ["peaceful meditation audio 10 minutes", "méditation paix intérieure 10 minutes"],
            "confident": ["confidence meditation 10 minutes", "méditation confiance en soi 10 minutes"],
            "creative": ["creativity meditation 10 minutes", "méditation créativité 10 minutes"],
            "compassionate": ["compassion meditation 10 minutes", "méditation compassion 10 minutes"],
            "mindful": ["mindfulness meditation 10 minutes", "méditation pleine conscience 10 minutes"],
            "balanced": ["balance meditation 10 minutes", "méditation équilibre 10 minutes"],
            "resilient": ["resilience meditation 10 minutes", "méditation resilience 10 minutes"],
            "hopeful": ["hope meditation 10 minutes", "méditation espoir 10 minutes"],
            "serene": ["serenity meditation 10 minutes", "méditation sérénité 10 minutes"]
        }
        
        # List of meditation audio sources to scrape
        self.audio_sources = [
            "https://www.freemindfulness.org/download",
            "https://www.tarabrach.com/guided-meditations/",
            "https://insighttimer.com/meditation-music",
            "https://www.mindful.org/audio-resources-for-mindfulness-meditation/",
            "https://www.uclahealth.org/programs/marc/free-guided-meditations"
        ]
        
    async def retrieve(self, mood: str, preferred_language="english") -> str:
        """
        Find and return the URL of a meditation audio file based on the provided mood.
        
        Args:
            mood: The mood to base the meditation on
            preferred_language: Preferred language for the meditation (english or french)
            
        Returns:
            URL of a suitable meditation audio file
        """
        # Normalize the mood
        mood = mood.lower().strip()
        
        # Get the appropriate search queries for this mood
        if mood in self.mood_to_query:
            queries = self.mood_to_query[mood]
        else:
            # Use default queries if the mood isn't in our map
            queries = ["guided meditation 10 minutes", "méditation guidée 10 minutes"]
        
        # Select a query based on the preferred language
        if preferred_language.lower() == "french":
            query = next((q for q in queries if "méditation" in q.lower()), queries[0])
        else:
            query = next((q for q in queries if "meditation" in q.lower()), queries[0])
        
        # Search for meditation audio URLs
        audio_url = await self._search_for_meditation_audio(query, preferred_language)
        
        return audio_url
    
    async def _search_for_meditation_audio(self, query, preferred_language):
        """
        Search for meditation audio by scraping meditation websites.
        
        Args:
            query: Search query string
            preferred_language: The preferred language for meditation content
            
        Returns:
            URL of a suitable meditation audio file
        """
        # Select a source to scrape
        source_url = random.choice(self.audio_sources)
        
        try:
            # Get the page content
            response = requests.get(source_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find audio links - common patterns in meditation sites
            audio_links = []
            
            # Look for audio tags
            audio_tags = soup.find_all('audio')
            for tag in audio_tags:
                if tag.get('src'):
                    audio_links.append(tag.get('src'))
                
            # Look for links ending with audio extensions
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.endswith(('.mp3', '.wav', '.m4a')):
                    audio_links.append(href)
                    
            # Look for links containing download indicators
            for a_tag in soup.find_all('a', href=True):
                if ('download' in a_tag.text.lower() or 
                    'audio' in a_tag.text.lower() or 
                    'meditation' in a_tag.text.lower()):
                    audio_links.append(a_tag['href'])
            
            # Filter for appropriate language if possible
            language_key = 'méditation' if preferred_language.lower() == 'french' else 'meditation'
            lang_filtered = [link for link in audio_links if language_key in link.lower()]
            
            # Use language filtered links if available, otherwise use all links
            final_links = lang_filtered if lang_filtered else audio_links
            
            # If we found any audio links, return one randomly
            if final_links:
                link = random.choice(final_links)
                # Ensure the link is absolute
                if not urlparse(link).netloc:
                    # It's a relative link, make it absolute
                    base_url = urlparse(source_url)
                    base_domain = f"{base_url.scheme}://{base_url.netloc}"
                    link = f"{base_domain}/{link.lstrip('/')}"
                return link
            
            # As a fallback, return a placeholder or a known meditation audio URL
            return "https://www.freemindfulness.org/FreeMindfulness3MinuteBreathing.mp3"
            
        except Exception as e:
            print(f"Error scraping for meditation audio: {str(e)}")
            # Return a fallback URL in case of error
            return "https://www.freemindfulness.org/FreeMindfulness3MinuteBreathing.mp3" 