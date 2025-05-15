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
import time

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
    1. Search YouTube for suitable meditation audio matching the mood and duration
    2. Download the audio file (typically around 10 minutes in length)
    3. Check the audio quality to ensure it meets standards
    4. Return a URL to the best matching meditation
    
    Returns JSON with audio URL and metadata.
    """
    try:
        orchestrator = MeditationOrchestrator(language=request.language)
        
        # Create a temporary file to store the meditation
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Generate the meditation
        meditation_result = await orchestrator.generate_meditation(
            request.mood, 
            language=request.language,
            output_path=temp_path
        )
        
        # meditation_result is now a tuple (path, source_info)
        meditation_path = meditation_result[0] if isinstance(meditation_result, tuple) else meditation_result
        source_info = meditation_result[1] if isinstance(meditation_result, tuple) and len(meditation_result) > 1 else None
        
        # Clean up resources
        await orchestrator.close()
        
        # Move the file to a static location for serving
        static_dir = Path(__file__).parent.parent / "static" / "meditations"
        static_dir.mkdir(exist_ok=True)
        
        # Create a unique filename based on mood, language and timestamp
        timestamp = int(time.time())
        filename = f"meditation_{request.mood}_{request.language}_{timestamp}.mp3"
        static_path = static_dir / filename
        
        # Move the file
        import shutil
        shutil.copy(meditation_path, static_path)
        
        # Clean up the temporary file
        os.unlink(meditation_path)
        
        # Return the audio URL and metadata
        audio_url = f"/static/meditations/{filename}"
        return {
            "status": "success",
            "audio_url": audio_url,
            "mood": request.mood,
            "language": request.language,
            "message": f"Your {request.mood} meditation is ready to play.",
            "note": "Find a quiet place, sit comfortably, and breathe deeply as you listen.",
            "source_info": source_info
        }
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