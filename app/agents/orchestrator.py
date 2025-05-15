import os
import tempfile
from pathlib import Path

from app.agents.script_generator import ScriptGeneratorAgent
from app.agents.meditation_review import MeditationReviewAgent
from app.agents.ambient_sound import AmbientSoundSelectorAgent
from app.agents.tts import TTSSynthesisAgent
from app.agents.audio_mixer import AudioMixerAgent

class MeditationOrchestrator:
    """
    Orchestrator that coordinates the workflow between all meditation generation agents.
    """
    
    def __init__(self):
        """
        Initialize all the required agents.
        """
        self.script_generator = ScriptGeneratorAgent()
        self.meditation_reviewer = MeditationReviewAgent()
        self.ambient_sound_selector = AmbientSoundSelectorAgent()
        self.tts_synthesizer = TTSSynthesisAgent()
        self.audio_mixer = AudioMixerAgent()
    
    async def generate_meditation(self, mood: str, output_path: str = None) -> str:
        """
        Generate a complete meditation audio file based on the provided mood.
        
        Args:
            mood: The mood to base the meditation on
            output_path: Path where the output audio file should be saved
            
        Returns:
            Path to the generated meditation audio file
        """
        # If no output path is provided, create a temporary file
        if output_path is None:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                output_path = temp_file.name
        
        # Step 1: Generate the initial script
        script = await self.script_generator.generate(mood)
        
        # Step 2: Review and improve the script
        reviewed_script = await self.meditation_reviewer.review(script, mood)
        
        # Step 3: Select an appropriate ambient sound
        ambient_sound_path = self.ambient_sound_selector.select(mood)
        
        # Step 4: Convert the script to speech
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as voice_temp:
            voice_audio_path = await self.tts_synthesizer.synthesize(
                reviewed_script, output_path=voice_temp.name
            )
        
        # Step 5: Mix the voice with the ambient sound
        mixed_audio_path = await self.audio_mixer.mix(
            voice_audio_path, ambient_sound_path, output_path=output_path
        )
        
        # Clean up temporary files
        if os.path.exists(voice_audio_path):
            os.unlink(voice_audio_path)
        
        return mixed_audio_path 