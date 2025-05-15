from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import tempfile
from pathlib import Path
# Now we can use the real orchestrator
from app.agents.orchestrator import MeditationOrchestrator

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Create static directory if it doesn't exist
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)

app = FastAPI(
    title="Daily Meditation API",
    description="Generate personalized meditations based on your mood using audio from Pixabay and Archive.org",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

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
    language: str = "english"  # Default to English if not specified
    
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Render the homepage with the mood selection interface.
    """
    moods = [
        "calm", "focused", "relaxed", "energized", "grateful", 
        "happy", "peaceful", "confident", "creative", "compassionate"
    ]
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "moods": moods}
    )

@app.post("/generate-meditation")
async def generate_meditation(request: MeditationRequest):
    """
    Generate a personalized meditation based on the provided mood and language preference.
    
    The API will:
    1. Search Pixabay and Archive.org for suitable meditation audio matching the mood
    2. Download the audio file (typically around 10 minutes in length)
    3. Check the audio quality to ensure it meets standards
    4. Return the best matching meditation
    
    Returns an MP3 audio file of the meditation.
    """
    try:
        orchestrator = MeditationOrchestrator(language=request.language)
        
        # Create a temporary file to store the meditation
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Generate the meditation
        meditation_path = await orchestrator.generate_meditation(
            request.mood, 
            language=request.language,
            output_path=temp_path
        )
        
        # Clean up resources
        await orchestrator.close()
        
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
                "Content-Disposition": f'attachment; filename="meditation_{request.mood}_{request.language}.mp3"'
            }
        )
    except Exception as e:
        # For debugging purposes, log the error
        import logging
        logging.error(f"Error generating meditation: {str(e)}")
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

@app.get("/available-languages")
async def available_languages():
    """
    Get the list of available languages for meditation audio.
    """
    languages = ["english", "french"]
    return {"languages": languages} 