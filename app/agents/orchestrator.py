import os
import tempfile
from pathlib import Path

from app.agents.audio_retriever import AudioRetrieverAgent
from app.agents.ambient_sound import AmbientSoundSelectorAgent
from app.agents.audio_mixer import AudioMixerAgent

class MeditationOrchestrator:
    """
    Orchestrator that coordinates the workflow between meditation generation agents.
    Uses web scraping to find 10-minute meditation audio files in French or English.
    """
    
    def __init__(self, language="english"):
        """
        Initialize all the required agents.
        
        Args:
            language: Preferred language for meditation audio (english or french)
        """
        self.audio_retriever = AudioRetrieverAgent()
        self.ambient_sound_selector = AmbientSoundSelectorAgent()
        self.audio_mixer = AudioMixerAgent()
        self.language = language
    
    async def generate_meditation(self, mood: str, language=None, output_path: str = None) -> str:
        """
        Generate a complete meditation audio file based on the provided mood.
        
        Args:
            mood: The mood to base the meditation on
            language: Preferred language (english or french)
            output_path: Path where the output audio file should be saved
            
        Returns:
            Path to the generated meditation audio file
        """
        # If no language is specified, use the default
        if language is None:
            language = self.language
            
        # If no output path is provided, create a temporary file
        if output_path is None:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                output_path = temp_file.name
        
        # Step 1: Retrieve meditation audio from the web
        meditation_audio_path = await self.audio_retriever.retrieve(mood, preferred_language=language)
        
        # Step 2: Select an appropriate ambient sound
        ambient_sound_path = self.ambient_sound_selector.select(mood)
        
        # Step 3: Mix the meditation audio with the ambient sound
        mixed_audio_path = await self.audio_mixer.mix(
            meditation_audio_path, ambient_sound_path, output_path=output_path
        )
        
        # Clean up temporary files
        if os.path.exists(meditation_audio_path) and meditation_audio_path != output_path:
            os.unlink(meditation_audio_path)
        
        return mixed_audio_path 