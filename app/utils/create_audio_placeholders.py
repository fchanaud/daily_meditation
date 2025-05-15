import os
from pathlib import Path

def create_audio_placeholders():
    """
    Create placeholder cached audio files for development.
    In production, these would be replaced with real meditation audio files from the web.
    """
    # Define combinations of moods and languages
    moods = [
        "calm", "focused", "relaxed", "energized", "grateful", 
        "happy", "peaceful", "confident", "creative", "compassionate",
        "mindful", "balanced", "resilient", "hopeful", "serene"
    ]
    
    languages = ["english", "french"]
    
    # Get the path to the cached audio directory
    cached_dir = Path(__file__).parent.parent / "assets" / "cached_audio"
    
    # Create the directory if it doesn't exist
    os.makedirs(cached_dir, exist_ok=True)
    
    # Create placeholder files for each mood and language combination
    for mood in moods:
        for language in languages:
            # Create a unique filename
            file_name = f"{mood}_{language}_placeholder.mp3"
            file_path = cached_dir / file_name
            
            # Create a placeholder file if it doesn't exist
            if not file_path.exists():
                # In a real project, you would download actual audio files
                # For now, create empty placeholder files
                file_path.touch()
                print(f"Created placeholder for {mood} meditation in {language}")

if __name__ == "__main__":
    create_audio_placeholders() 