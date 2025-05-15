import os
import tempfile
from pathlib import Path
import subprocess
from pydub import AudioSegment

class AudioMixerAgent:
    """
    Agent for mixing meditation audio with ambient sounds to create the final meditation audio.
    """
    
    def __init__(self):
        """
        Initialize the audio mixer agent.
        """
        pass
    
    async def mix(self, meditation_path: str, ambient_path: str, output_path: str = None) -> str:
        """
        Mix the meditation audio with the ambient sound to create the final meditation audio.
        
        Args:
            meditation_path: Path to the meditation audio file (MP3 or WAV)
            ambient_path: Path to the ambient sound file (MP3 or WAV)
            output_path: Path where the output audio file should be saved (MP3)
            
        Returns:
            Path to the generated mixed audio file (MP3)
        """
        # If no output path is provided, create a temporary file
        if output_path is None:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                output_path = temp_file.name
                
        print(f"Mixing meditation audio: {meditation_path}")
        print(f"With ambient sound: {ambient_path}")
        print(f"Output will be saved to: {output_path}")
        
        try:
            # Check if both files exist
            if not os.path.exists(meditation_path) or not os.path.isfile(meditation_path):
                print(f"Warning: Meditation audio file does not exist: {meditation_path}")
                Path(output_path).touch()
                return output_path
                
            if not os.path.exists(ambient_path) or not os.path.isfile(ambient_path):
                print(f"Warning: Ambient sound file does not exist: {ambient_path}")
                # If ambient sound doesn't exist but meditation does, just copy the meditation
                if os.path.exists(meditation_path) and os.path.getsize(meditation_path) > 0:
                    import shutil
                    shutil.copy(meditation_path, output_path)
                else:
                    Path(output_path).touch()
                return output_path
            
            # Check if files are empty (placeholders)
            if os.path.getsize(meditation_path) == 0 or os.path.getsize(ambient_path) == 0:
                print(f"Warning: One or both audio files are empty placeholders")
                # If meditation file has content, just use that
                if os.path.getsize(meditation_path) > 0:
                    import shutil
                    shutil.copy(meditation_path, output_path)
                else:
                    Path(output_path).touch()
                return output_path
            
            # Load the audio files
            meditation = AudioSegment.from_file(meditation_path)
            ambient = AudioSegment.from_file(ambient_path)
            
            # Loop the ambient sound if it's shorter than the meditation track
            if len(ambient) < len(meditation):
                loops_needed = (len(meditation) // len(ambient)) + 1
                ambient = ambient * loops_needed
            
            # Trim the ambient sound to match the meditation track length
            ambient = ambient[:len(meditation)]
            
            # Lower the volume of the ambient sound (to -15dB compared to the meditation)
            ambient = ambient - 15
            
            # Mix the two tracks
            mixed = meditation.overlay(ambient)
            
            # Export to MP3
            mixed.export(output_path, format="mp3")
            print(f"Successfully mixed audio and saved to: {output_path}")
            
        except Exception as e:
            print(f"Error mixing audio: {str(e)}")
            # Create a backup plan - if meditation file exists and has content, just use that
            if os.path.exists(meditation_path) and os.path.getsize(meditation_path) > 0:
                try:
                    import shutil
                    shutil.copy(meditation_path, output_path)
                    print(f"Fallback: Copied meditation audio to output without mixing")
                except Exception:
                    Path(output_path).touch()
            else:
                # Last resort - create an empty file
                Path(output_path).touch()
        
        return output_path 