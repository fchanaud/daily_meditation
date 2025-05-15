from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
from app.agents.orchestrator import MeditationOrchestrator

app = FastAPI(
    title="Daily Meditation API",
    description="Generate personalized meditations based on your mood",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MeditationRequest(BaseModel):
    mood: str
    
@app.get("/")
async def root():
    return {"message": "Welcome to the Daily Meditation API"}

@app.post("/generate-meditation")
async def generate_meditation(request: MeditationRequest):
    """
    Generate a personalized meditation based on the provided mood.
    
    Returns an MP3 audio file of the meditation.
    """
    try:
        orchestrator = MeditationOrchestrator()
        
        # Create a temporary file to store the meditation
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Generate the meditation
        meditation_path = await orchestrator.generate_meditation(request.mood, output_path=temp_path)
        
        # Read the meditation file
        with open(meditation_path, "rb") as f:
            audio_data = f.read()
        
        # Clean up the temporary file
        os.unlink(meditation_path)
        
        # Return the audio file
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="meditation_{request.mood}.mp3"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate meditation: {str(e)}")

@app.get("/available-moods")
async def available_moods():
    """
    Get the list of available moods that can be used for meditation generation.
    """
    moods = [
        "calm", "focused", "relaxed", "energized", "grateful", 
        "happy", "peaceful", "confident", "creative", "compassionate",
        "mindful", "balanced", "resilient", "hopeful", "serene"
    ]
    return {"moods": moods} 