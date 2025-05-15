import os
import random
import logging
import asyncio
import time
import json
from pathlib import Path
import jwt
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AppleMusicAgent:
    """
    Agent for retrieving meditation audio from Apple Music API.
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize the Apple Music API agent.
        
        Args:
            cache_dir: Directory to cache downloaded audio files
        """
        if cache_dir is None:
            self.cache_dir = Path(__file__).parent.parent / "assets" / "cached_audio"
        else:
            self.cache_dir = Path(cache_dir)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Get Apple Music API credentials from environment
        self.team_id = os.getenv("APPLE_TEAM_ID")
        self.key_id = os.getenv("APPLE_KEY_ID")
        self.private_key = os.getenv("APPLE_PRIVATE_KEY")
        
        # Cache for search results
        self.search_cache_file = self.cache_dir / "apple_music_cache.json"
        self.search_cache = self._load_search_cache()
        
        # Map moods to search queries for Apple Music
        self.mood_to_query = {
            "calm": ["calm meditation music", "calming meditation guided", "peaceful meditation"],
            "focused": ["focus meditation", "concentration meditation", "focus meditation guided"],
            "relaxed": ["relaxing meditation", "relaxation guided meditation", "sleep meditation"],
            "energized": ["energizing meditation music", "morning meditation", "energy boost meditation"],
            "grateful": ["gratitude meditation", "gratitude practice guided", "appreciation meditation"],
            "happy": ["happiness meditation", "joyful meditation guided", "positive energy meditation"],
            "peaceful": ["peaceful meditation", "peace meditation guided", "tranquil meditation"],
            "confident": ["confidence meditation", "self-esteem meditation", "empowerment meditation"],
            "creative": ["creativity meditation", "creative flow meditation", "inspiration meditation"],
            "compassionate": ["compassion meditation", "loving-kindness meditation", "heart meditation"]
        }
        
        # List of audio tracks that have been recently used
        self.recently_used_tracks = []
        
        # Developer token and expiration
        self._developer_token = None
        self._token_expiration = None
    
    def _load_search_cache(self):
        """
        Load search cache from file.
        
        Returns:
            Dict containing the search cache
        """
        if self.search_cache_file.exists():
            try:
                with open(self.search_cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading search cache: {str(e)}")
        
        return {}
    
    def _save_search_cache(self):
        """
        Save search cache to file.
        """
        try:
            with open(self.search_cache_file, 'w') as f:
                json.dump(self.search_cache, f)
        except Exception as e:
            logger.error(f"Error saving search cache: {str(e)}")
    
    def _generate_developer_token(self):
        """
        Generate a developer token for Apple Music API.
        
        Returns:
            String containing the developer token
        """
        if not self.team_id or not self.key_id or not self.private_key:
            logger.error("Apple Music API credentials not properly configured")
            return None
        
        # Set token expiration to 15 minutes from now
        expiration_time = datetime.now() + timedelta(minutes=15)
        self._token_expiration = expiration_time
        
        # Prepare the token payload
        payload = {
            'iss': self.team_id,
            'iat': int(time.time()),
            'exp': int(expiration_time.timestamp()),
            'sub': 'daily-meditation-app' # Your app identifier
        }
        
        try:
            # Create the JWT token
            token = jwt.encode(
                payload,
                self.private_key,
                algorithm='ES256',
                headers={
                    'kid': self.key_id,
                    'alg': 'ES256'
                }
            )
            
            return token
        except Exception as e:
            logger.error(f"Error generating developer token: {str(e)}")
            return None
    
    def _get_developer_token(self):
        """
        Get a valid developer token, generating a new one if needed.
        
        Returns:
            String containing the developer token
        """
        # Check if token is expired or not generated yet
        if not self._developer_token or not self._token_expiration or datetime.now() >= self._token_expiration:
            self._developer_token = self._generate_developer_token()
        
        return self._developer_token
    
    async def _search_apple_music(self, query, limit=20, types=None):
        """
        Search Apple Music for tracks matching the query.
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 20)
            types: Types of content to search for (default: songs)
            
        Returns:
            Dict containing search results
        """
        # Default to songs if no types provided
        if types is None:
            types = ['songs']
        
        # Get developer token
        token = self._get_developer_token()
        if not token:
            logger.error("Failed to generate developer token")
            return None
        
        # Prepare the API endpoint
        types_str = ','.join(types)
        url = f"https://api.music.apple.com/v1/catalog/us/search"
        params = {
            'term': query,
            'limit': limit,
            'types': types_str
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            # Make the API request
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"Apple Music search successful for query: {query}")
                    return response.json()
                else:
                    logger.error(f"Apple Music search failed: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            logger.error(f"Error searching Apple Music: {str(e)}")
            return None
    
    async def _filter_meditation_tracks(self, search_results):
        """
        Filter search results to find suitable meditation tracks (8-15 minutes).
        
        Args:
            search_results: Search results from Apple Music
            
        Returns:
            List of filtered meditation tracks
        """
        filtered_tracks = []
        
        if not search_results or 'results' not in search_results:
            return filtered_tracks
        
        # Check if songs data exists
        if 'songs' not in search_results['results']:
            return filtered_tracks
        
        # Process each track
        for track in search_results['results']['songs']['data']:
            try:
                # Check duration (8-15 minutes = 480000-900000 milliseconds)
                duration_ms = track['attributes'].get('durationInMillis', 0)
                
                if 480000 <= duration_ms <= 900000:
                    # Check if the track has been recently used
                    if track['id'] not in self.recently_used_tracks:
                        filtered_tracks.append(track)
            except Exception as e:
                logger.error(f"Error processing track: {str(e)}")
                continue
        
        logger.info(f"Found {len(filtered_tracks)} suitable meditation tracks")
        return filtered_tracks
    
    async def find_meditation(self, mood, language="english"):
        """
        Find a suitable meditation based on mood and language.
        
        Args:
            mood: User's mood
            language: Preferred language (default: english)
            
        Returns:
            Tuple of (track_url, metadata)
        """
        # Create a cache key
        cache_key = f"{mood}_{language}"
        
        # Check if we have cached results for this mood and language
        if cache_key in self.search_cache and self.search_cache[cache_key]:
            logger.info(f"Using cached Apple Music results for mood: {mood}, language: {language}")
            
            # Avoid returning the same tracks consecutively
            available_tracks = [track for track in self.search_cache[cache_key] 
                               if track['id'] not in self.recently_used_tracks]
            
            # If all tracks have been recently used, reset and use all
            if not available_tracks:
                logger.info("All cached tracks have been recently used, resetting filter")
                available_tracks = self.search_cache[cache_key]
            
            # Select a random track
            if available_tracks:
                selected_track = random.choice(available_tracks)
                
                # Add to recently used tracks (limit to last 5)
                self.recently_used_tracks.append(selected_track['id'])
                if len(self.recently_used_tracks) > 5:
                    self.recently_used_tracks.pop(0)
                
                return self._prepare_track_response(selected_track)
        
        # Get appropriate search queries for this mood
        if mood in self.mood_to_query:
            queries = self.mood_to_query[mood]
        else:
            # Default queries if mood isn't in our predefined list
            queries = ["meditation music", "mindfulness meditation", "relaxing music"]
        
        # Add language to queries if it's not English
        if language.lower() != "english":
            queries = [f"{query} {language}" for query in queries]
        
        # Try Apple Music search with our queries
        all_tracks = []
        
        for query in queries:
            logger.info(f"Searching Apple Music with query: {query}")
            search_results = await self._search_apple_music(query)
            
            if search_results:
                # Filter suitable meditation tracks
                filtered_tracks = await self._filter_meditation_tracks(search_results)
                all_tracks.extend(filtered_tracks)
            
            await asyncio.sleep(0.5)  # Small delay between requests
        
        # If we found suitable tracks
        if all_tracks:
            # Cache the results for future use
            self.search_cache[cache_key] = all_tracks
            self._save_search_cache()
            
            # Select a random track
            selected_track = random.choice(all_tracks)
            
            # Add to recently used tracks (limit to last 5)
            self.recently_used_tracks.append(selected_track['id'])
            if len(self.recently_used_tracks) > 5:
                self.recently_used_tracks.pop(0)
            
            return self._prepare_track_response(selected_track)
        
        # If no suitable tracks found, use a fallback
        logger.warning(f"No suitable Apple Music meditation tracks found for {mood}")
        return (None, None)
    
    def _prepare_track_response(self, track):
        """
        Prepare the track response from Apple Music data.
        
        Args:
            track: Apple Music track data
            
        Returns:
            Tuple of (track_url, metadata)
        """
        # Get the preview URL
        preview_url = None
        if 'attributes' in track and 'previews' in track['attributes'] and track['attributes']['previews']:
            preview_url = track['attributes']['previews'][0]['url']
        
        # Build metadata
        metadata = {
            'apple_music_id': track['id'],
            'title': track['attributes'].get('name', 'Unknown Meditation'),
            'artist': track['attributes'].get('artistName', 'Unknown Artist'),
            'album': track['attributes'].get('albumName', 'Unknown Album'),
            'duration_ms': track['attributes'].get('durationInMillis', 0),
            'artwork_url': track['attributes'].get('artwork', {}).get('url', None),
            'apple_music_url': track['attributes'].get('url', None)
        }
        
        return (preview_url, metadata)
    
    async def get_playback_url(self, track_id, user_token=None):
        """
        Get a playback URL for a track with user authentication.
        
        Args:
            track_id: Apple Music track ID
            user_token: User's Apple Music token (optional)
            
        Returns:
            Playback URL for the track
        """
        # Note: Getting actual playback URLs requires user authentication
        # This is a placeholder for future implementation
        
        # For now, return None - we'll use the preview URL from find_meditation
        logger.warning("Full Apple Music playback requires user authentication - using preview URL")
        return None
    
    async def get_similar_tracks(self, track_id, limit=10):
        """
        Get similar tracks to the specified track.
        
        Args:
            track_id: Apple Music track ID
            limit: Maximum number of results (default: 10)
            
        Returns:
            List of similar tracks
        """
        # Get developer token
        token = self._get_developer_token()
        if not token:
            logger.error("Failed to generate developer token")
            return []
        
        # Prepare the API endpoint
        url = f"https://api.music.apple.com/v1/catalog/us/songs/{track_id}/recommendations"
        params = {
            'limit': limit
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            # Make the API request
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"Apple Music recommendations retrieved for track: {track_id}")
                    result = response.json()
                    
                    # Process and return the recommendations
                    if 'data' in result:
                        return result['data']
                    return []
                else:
                    logger.error(f"Apple Music recommendations failed: {response.status_code} - {response.text}")
                    return []
                
        except Exception as e:
            logger.error(f"Error getting Apple Music recommendations: {str(e)}")
            return [] 