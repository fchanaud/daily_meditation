"""
MeditationOrchestrator module for coordinating the meditation generation workflow.
This module orchestrates the process of finding and serving meditation videos.
"""

import os
import logging
from pathlib import Path
import asyncio

from app.agents.openai_meditation_agent import OpenAIMeditationAgent
from app.agents.feedback_collector import FeedbackCollectorAgent
from app.utils.db import save_meditation_session, get_user_watched_videos

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MeditationOrchestrator:
    """
    Orchestrator that coordinates finding meditation videos and collecting feedback.
    Uses OpenAI to find YouTube videos for meditation based on mood.
    """
    
    def __init__(self, language="english"):
        """
        Initialize the meditation orchestrator and its component agents.
        
        Args:
            language: Default language for meditations (english or french)
        """
        # Set default language
        self.language = language
        
        # Initialize agents
        self.openai_agent = OpenAIMeditationAgent()
        self.feedback_collector = FeedbackCollectorAgent()
        
        # Track the current meditation metadata
        self.current_meditation = None
    
    async def generate_meditation(self, mood, language=None, user_id=None):
        """
        Generate a meditation based on the provided mood.
        
        This method uses OpenAI to find a YouTube meditation video:
        1. Ask OpenAI for a YouTube URL based on mood and language
        2. Format the response for embedding in the web app
        
        Args:
            mood: The mood to base the meditation on
            language: Language preference (defaults to the instance language)
            user_id: Optional user identifier to avoid showing previously watched videos
            
        Returns:
            Dictionary containing YouTube URL and metadata
        """
        # Use instance language if none provided
        language = language or self.language
        logger.info(f"Finding meditation for mood: {mood}, language: {language}")
        
        try:
            # Get list of previously watched videos for this user if user_id is provided
            watched_videos = []
            if user_id:
                watched_videos = await get_user_watched_videos(user_id)
                logger.info(f"Found {len(watched_videos)} previously watched videos for user")
            
            # Find a meditation video URL using OpenAI
            youtube_url, source_info = await self.openai_agent.find_meditation(
                mood, 
                language,
                watched_videos=watched_videos
            )
            
            # Add mood to the metadata for feedback
            if source_info:
                track_metadata = {
                    'title': source_info.get('title', 'Meditation Video'),
                    'artist': 'YouTube Creator',
                    'mood': mood,
                    'youtube_url': youtube_url,
                    'duration_ms': 600000  # Default 10 minutes
                }
                
                # Store current meditation for feedback collection
                self.current_meditation = track_metadata
            
            # Note: We don't save to database here anymore, it will be saved when watching is complete
            logger.info(f"Found meditation video URL: {youtube_url}")
            
            # Return the YouTube URL and metadata
            return youtube_url, source_info
            
        except Exception as e:
            logger.error(f"Error generating meditation: {str(e)}")
            
            # Fallback URL if there's an error
            fallback_url = "https://www.youtube.com/watch?v=O-6f5wQXSu8"
            fallback_info = {
                'youtube_url': fallback_url,
                'title': 'Fallback Meditation Video'
            }
            
            # Set current meditation metadata for the fallback
            self.current_meditation = {
                'title': 'Fallback Meditation',
                'artist': 'Daily Meditation',
                'mood': mood,
                'youtube_url': fallback_url,
                'duration_ms': 600000  # 10 minutes
            }
            
            return fallback_url, fallback_info
    
    async def collect_feedback(self, user_id, feedback_responses):
        """
        Collect and save user feedback about the meditation.
        
        Args:
            user_id: Identifier for the user
            feedback_responses: Dictionary of user responses to feedback questions
            
        Returns:
            Boolean indicating success
        """
        if not self.current_meditation:
            logger.warning("No current meditation data available for feedback")
            return False
        
        # Add user ID to feedback data
        feedback_responses['user_id'] = user_id
        
        # Save the feedback using the feedback collector
        success = self.feedback_collector.save_feedback(feedback_responses, self.current_meditation)
        
        if success:
            logger.info(f"Saved feedback from user {user_id}")
            
            # Process the feedback with the OpenAI agent to improve future recommendations
            await self.openai_agent.process_feedback(feedback_responses, self.current_meditation)
        else:
            logger.error(f"Failed to save feedback from user {user_id}")
        
        return success
    
    def get_feedback_questions(self):
        """
        Get feedback questions for the current meditation.
        
        Returns:
            List of feedback questions
        """
        return self.feedback_collector.get_feedback_questions(self.current_meditation)
    
    def should_show_feedback_form(self, user_id):
        """
        Determine if feedback form should be shown to the user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Boolean indicating if feedback form should be shown
        """
        return self.feedback_collector.should_show_feedback_form(user_id)
    
    async def close(self):
        """
        Clean up resources when shutting down.
        """
        # Any cleanup tasks needed
        pass
    
    def _get_or_create_fallback(self, mood, language):
        """
        Get a guaranteed fallback file path, creating the directory if it doesn't exist.
        
        Args:
            mood: The mood for the fallback
            language: The language for the fallback
            
        Returns:
            Path to the fallback file
        """
        fallback_dir = self.cache_dir / "fallback"
        os.makedirs(fallback_dir, exist_ok=True)
        
        # Use our simplest fallback
        return str(Path(__file__).parent.parent / "assets" / "fallback_meditation.mp3")
    
    async def save_completed_meditation(self, user_id=None):
        """
        Save the current meditation to the database after it has been watched.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Boolean indicating success
        """
        if not self.current_meditation:
            logger.warning("No current meditation data available to save")
            return False
        
        try:
            # Extract data from current meditation
            mood = self.current_meditation.get('mood', 'unknown')
            youtube_url = self.current_meditation.get('youtube_url', None)
            
            # Save the meditation session to the database
            await save_meditation_session(
                mood=mood,
                language=self.language,
                youtube_url=youtube_url,
                audio_url=None,
                user_id=user_id
            )
            
            logger.info(f"Saved completed meditation with URL: {youtube_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving completed meditation: {str(e)}")
            return False 