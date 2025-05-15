import os
import random
from pathlib import Path

class AmbientSoundSelectorAgent:
    """
    Agent for selecting ambient sounds to accompany meditation scripts.
    Uses a mapping of moods to ambient sound categories.
    """
    
    def __init__(self, sounds_dir=None):
        if sounds_dir is None:
            # Use the default sounds directory
            self.sounds_dir = Path(__file__).parent.parent / "assets" / "ambient_sounds"
        else:
            self.sounds_dir = Path(sounds_dir)
            
        # Create a mapping of moods to ambient sound categories
        self.mood_to_sound_map = {
            "calm": ["gentle_waves", "soft_rain", "forest_breeze"],
            "focused": ["light_rain", "white_noise", "gentle_creek"],
            "relaxed": ["beach_waves", "summer_night", "gentle_rain"],
            "energized": ["flowing_river", "morning_birds", "spring_breeze"],
            "grateful": ["garden_sounds", "gentle_stream", "light_wind"],
            "happy": ["birds_chirping", "summer_meadow", "gentle_waves"],
            "peaceful": ["soft_rain", "quiet_forest", "gentle_stream"],
            "confident": ["ocean_waves", "steady_rain", "mountain_wind"],
            "creative": ["flowing_water", "light_rain", "forest_sounds"],
            "compassionate": ["gentle_waves", "soft_breeze", "quiet_garden"],
            "mindful": ["zen_garden", "light_rain", "forest_ambience"],
            "balanced": ["gentle_creek", "soft_rain", "light_wind"],
            "resilient": ["ocean_waves", "mountain_stream", "steady_rain"],
            "hopeful": ["morning_birds", "gentle_breeze", "spring_creek"],
            "serene": ["gentle_stream", "soft_rain", "quiet_forest"]
        }
        
        # Default fallback sounds if a specific mood isn't found
        self.default_sounds = ["gentle_waves", "soft_rain", "light_wind"]
        
        # Ensure the sounds directory exists (create it if not)
        os.makedirs(self.sounds_dir, exist_ok=True)
        
    def select(self, mood: str) -> str:
        """
        Select an ambient sound based on the provided mood.
        
        Args:
            mood: The mood to base the ambient sound selection on
            
        Returns:
            Path to the selected ambient sound file
        """
        # Normalize the mood input
        mood = mood.lower().strip()
        
        # Get the list of appropriate sound categories for this mood
        sound_categories = self.mood_to_sound_map.get(mood, self.default_sounds)
        
        # Randomly select one of the sound categories
        selected_category = random.choice(sound_categories)
        
        # In a real implementation, we would look for actual files in the sounds directory
        # For now, we'll just return a placeholder path
        # In a production system, you would add real ambient sound files to the sounds directory
        
        # Since we don't have actual sound files yet, we'll just return the selected category
        # In production, you would check for files of that category and select one
        placeholder_path = self.sounds_dir / f"{selected_category}.mp3"
        
        # Create a placeholder file if it doesn't exist
        if not placeholder_path.exists():
            # In a production system, you would have real sound files
            # For now, just create an empty file as a placeholder
            placeholder_path.touch()
            
        return str(placeholder_path) 