import logging
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeedbackCollectorAgent:
    """
    Agent for collecting and managing user feedback on meditation sessions.
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize the feedback collector agent.
        
        Args:
            data_dir: Directory to store feedback data
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / "assets" / "feedback_data"
        else:
            self.data_dir = Path(data_dir)
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Feedback data file
        self.feedback_file = self.data_dir / "meditation_feedback.json"
        self.feedback_data = self._load_feedback_data()
        
        # Predefined feedback questions
        self.feedback_questions = [
            "How would you rate today's meditation from 1-5?",
            "Did this meditation help with your mood?",
            "Would you like more meditations like this one?",
            "What would make your meditation experience better?"
        ]
    
    def _load_feedback_data(self) -> Dict:
        """
        Load feedback data from file.
        
        Returns:
            Dict containing feedback data
        """
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading feedback data: {str(e)}")
        
        # Initialize with empty structure
        return {
            "feedback_entries": [],
            "track_ratings": {},
            "preference_data": {
                "preferred_moods": {},
                "preferred_artists": {},
                "preferred_durations": {}
            }
        }
    
    def _save_feedback_data(self) -> bool:
        """
        Save feedback data to file.
        
        Returns:
            Boolean indicating success
        """
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving feedback data: {str(e)}")
            return False
    
    def get_feedback_questions(self, track_metadata=None) -> List[str]:
        """
        Get appropriate feedback questions for a meditation session.
        
        Args:
            track_metadata: Metadata about the meditation track (optional)
            
        Returns:
            List of feedback questions
        """
        # Start with basic questions
        questions = self.feedback_questions.copy()
        
        # Add track-specific questions if metadata is available
        if track_metadata:
            if 'artist' in track_metadata:
                questions.append(f"Did you enjoy this meditation by {track_metadata['artist']}?")
            
            if 'duration_ms' in track_metadata:
                duration_min = round(track_metadata['duration_ms'] / 60000)
                questions.append(f"Was {duration_min} minutes a good length for your meditation?")
        
        return questions
    
    def save_feedback(self, feedback_responses: Dict, track_metadata: Dict) -> bool:
        """
        Save user feedback for a meditation session.
        
        Args:
            feedback_responses: User's responses to feedback questions
            track_metadata: Metadata about the meditation track
            
        Returns:
            Boolean indicating success
        """
        try:
            # Prepare feedback entry
            timestamp = datetime.now().isoformat()
            
            # Track identifier - use YouTube URL as track ID
            if 'youtube_url' in track_metadata:
                track_id = track_metadata['youtube_url']
            else:
                track_id = "unknown"
            
            feedback_entry = {
                "timestamp": timestamp,
                "track_id": track_id,
                "track_metadata": track_metadata,
                "responses": feedback_responses
            }
            
            # Add to feedback entries
            self.feedback_data["feedback_entries"].append(feedback_entry)
            
            # Update track ratings if rating was provided
            if "rating" in feedback_responses and track_id != "unknown":
                if track_id not in self.feedback_data["track_ratings"]:
                    self.feedback_data["track_ratings"][track_id] = []
                
                self.feedback_data["track_ratings"][track_id].append({
                    "timestamp": timestamp,
                    "rating": feedback_responses["rating"]
                })
            
            # Update preference data
            self._update_preference_data(feedback_responses, track_metadata)
            
            # Save to file
            return self._save_feedback_data()
            
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            return False
    
    def _update_preference_data(self, feedback_responses: Dict, track_metadata: Dict) -> None:
        """
        Update user preference data based on feedback.
        
        Args:
            feedback_responses: User's responses to feedback questions
            track_metadata: Metadata about the meditation track
        """
        preference_data = self.feedback_data["preference_data"]
        
        # Only update preferences if we have a positive rating (4-5)
        if "rating" in feedback_responses:
            rating = feedback_responses.get("rating")
            try:
                rating_value = int(rating)
                is_positive = rating_value >= 4
                is_negative = rating_value <= 2
                
                # Update preferred moods
                if "mood" in track_metadata:
                    mood = track_metadata["mood"]
                    if mood not in preference_data["preferred_moods"]:
                        preference_data["preferred_moods"][mood] = {"count": 0, "positive": 0, "negative": 0}
                    
                    preference_data["preferred_moods"][mood]["count"] += 1
                    if is_positive:
                        preference_data["preferred_moods"][mood]["positive"] += 1
                    if is_negative:
                        preference_data["preferred_moods"][mood]["negative"] += 1
                
                # Update preferred artists
                if "artist" in track_metadata:
                    artist = track_metadata["artist"]
                    if artist not in preference_data["preferred_artists"]:
                        preference_data["preferred_artists"][artist] = {"count": 0, "positive": 0, "negative": 0}
                    
                    preference_data["preferred_artists"][artist]["count"] += 1
                    if is_positive:
                        preference_data["preferred_artists"][artist]["positive"] += 1
                    if is_negative:
                        preference_data["preferred_artists"][artist]["negative"] += 1
                
                # Update preferred durations
                if "duration_ms" in track_metadata:
                    # Group durations into buckets (9-10 min, 10-11 min, etc.)
                    duration_min = round(track_metadata["duration_ms"] / 60000)
                    duration_bucket = f"{duration_min}-{duration_min+1}min"
                    
                    if duration_bucket not in preference_data["preferred_durations"]:
                        preference_data["preferred_durations"][duration_bucket] = {"count": 0, "positive": 0, "negative": 0}
                    
                    preference_data["preferred_durations"][duration_bucket]["count"] += 1
                    if is_positive:
                        preference_data["preferred_durations"][duration_bucket]["positive"] += 1
                    if is_negative:
                        preference_data["preferred_durations"][duration_bucket]["negative"] += 1
                    
            except ValueError:
                # Rating wasn't a number, skip preference updates
                pass
    
    def get_personalized_recommendations(self) -> Dict:
        """
        Generate personalized recommendations based on feedback history.
        
        Returns:
            Dict containing recommendation data
        """
        recommendations = {
            "preferred_moods": [],
            "preferred_artists": [],
            "preferred_durations": []
        }
        
        preference_data = self.feedback_data["preference_data"]
        
        # Find top moods
        moods = list(preference_data["preferred_moods"].items())
        # Sort by positive ratings
        moods.sort(key=lambda x: x[1]["positive"], reverse=True)
        recommendations["preferred_moods"] = [mood for mood, data in moods[:3]]
        
        # Find top artists
        artists = list(preference_data["preferred_artists"].items())
        # Sort by positive ratings
        artists.sort(key=lambda x: x[1]["positive"], reverse=True)
        recommendations["preferred_artists"] = [artist for artist, data in artists[:3]]
        
        # Find top durations
        durations = list(preference_data["preferred_durations"].items())
        # Sort by positive ratings
        durations.sort(key=lambda x: x[1]["positive"], reverse=True)
        recommendations["preferred_durations"] = [duration for duration, data in durations[:3]]
        
        return recommendations
    
    def should_show_feedback_form(self, user_id: str) -> bool:
        """
        Determine if feedback form should be shown to the user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Boolean indicating if feedback form should be shown
        """
        # Check when the user last provided feedback
        last_feedback_time = None
        
        for entry in reversed(self.feedback_data["feedback_entries"]):
            if entry.get("user_id") == user_id:
                last_feedback_time = entry.get("timestamp")
                break
        
        if not last_feedback_time:
            # No previous feedback, should show form
            return True
        
        # Convert timestamp to datetime
        try:
            last_feedback_datetime = datetime.fromisoformat(last_feedback_time)
            now = datetime.now()
            
            # Check if it's been more than 1 day since last feedback
            time_diff = now - last_feedback_datetime
            return time_diff.days >= 1
            
        except ValueError:
            # Invalid timestamp format, show feedback form
            return True 