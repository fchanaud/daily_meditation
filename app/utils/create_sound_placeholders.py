import os
from pathlib import Path

def create_sound_placeholders():
    """
    Create placeholder sound files for development.
    In production, these would be replaced with real ambient sound files.
    """
    # Define the ambient sound categories
    sound_categories = [
        "gentle_waves", "soft_rain", "forest_breeze",
        "light_rain", "white_noise", "gentle_creek",
        "beach_waves", "summer_night", "gentle_rain",
        "flowing_river", "morning_birds", "spring_breeze",
        "garden_sounds", "gentle_stream", "light_wind",
        "birds_chirping", "summer_meadow",
        "peaceful_forest", "quiet_forest", "quiet_garden",
        "zen_garden", "forest_ambience",
        "mountain_stream", "steady_rain", "mountain_wind",
        "flowing_water", "forest_sounds", "spring_creek",
        "ocean_waves"
    ]
    
    # Get the path to the ambient sounds directory
    sounds_dir = Path(__file__).parent.parent / "assets" / "ambient_sounds"
    
    # Create the directory if it doesn't exist
    os.makedirs(sounds_dir, exist_ok=True)
    
    # Create a placeholder file for each sound category
    for category in sound_categories:
        sound_path = sounds_dir / f"{category}.mp3"
        if not sound_path.exists():
            # In a real project, you would download or include actual sound files
            # For now, create empty placeholder files
            sound_path.touch()
            print(f"Created placeholder for {category}")

if __name__ == "__main__":
    create_sound_placeholders() 