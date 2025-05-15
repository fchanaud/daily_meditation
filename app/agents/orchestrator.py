import os
import tempfile
from pathlib import Path

from app.agents.audio_retriever import AudioRetrieverAgent
from app.agents.audio_downloader import AudioDownloaderAgent
from app.agents.audio_quality_checker import AudioQualityCheckerAgent

class MeditationOrchestrator:
    """
    Orchestrator that coordinates the workflow between meditation generation agents.
    Uses web scraping to find 10-minute meditation audio files in French or English,
    downloads them, and checks their quality.
    """
    
    def __init__(self, language="english"):
        """
        Initialize all the required agents.
        
        Args:
            language: Preferred language for meditation audio (english or french)
        """
        self.audio_retriever = AudioRetrieverAgent()
        self.audio_downloader = AudioDownloaderAgent()
        self.audio_quality_checker = AudioQualityCheckerAgent()
        self.language = language
    
    async def generate_meditation(self, mood: str, language=None, output_path: str = None) -> str:
        """
        Generate a meditation audio file based on the provided mood.
        
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
        
        # Store temporary files to clean up later
        temp_files = []
        final_audio_path = None
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                print(f"Attempt {attempt+1}/{max_attempts} to find a suitable meditation audio")
                
                # Step 1: Retrieve meditation audio URL from the web
                meditation_audio_url = await self.audio_retriever.retrieve(mood, preferred_language=language)
                
                # Step 2: Download the meditation audio file
                meditation_audio_path = await self.audio_downloader.download(
                    meditation_audio_url, 
                    mood=mood, 
                    language=language
                )
                temp_files.append(meditation_audio_path)
                
                # Step 3: Check audio quality
                quality_result = await self.audio_quality_checker.check_quality(meditation_audio_path)
                
                if quality_result["is_acceptable"]:
                    print(f"Found acceptable meditation audio: {meditation_audio_path}")
                    print(f"Audio details: {quality_result['details']}")
                    
                    # This is our final file - copy it to the output path if needed
                    if meditation_audio_path != output_path:
                        import shutil
                        shutil.copy(meditation_audio_path, output_path)
                    
                    final_audio_path = output_path
                    break
                else:
                    print(f"Rejected audio file due to quality issues: {quality_result['issues']}")
                    # Continue to next attempt
            except Exception as e:
                print(f"Error in attempt {attempt+1}: {str(e)}")
                # Continue to next attempt
        
        # If we couldn't find a suitable file after all attempts
        if final_audio_path is None:
            print("Failed to find a suitable meditation audio file after all attempts")
            # Use the last downloaded file as a fallback if available
            if len(temp_files) > 0 and os.path.exists(temp_files[-1]):
                import shutil
                shutil.copy(temp_files[-1], output_path)
                final_audio_path = output_path
            else:
                # Create an empty placeholder as a last resort
                Path(output_path).touch()
                final_audio_path = output_path
        
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file) and temp_file != output_path:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
        
        return final_audio_path 