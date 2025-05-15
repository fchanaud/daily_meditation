from fastapi import FastAPI, HTTPException, Response, Request, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
# Now we can use the real orchestrator
from app.agents.orchestrator import MeditationOrchestrator
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Create static directory if it doesn't exist
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)

app = FastAPI(
    title="Daily Meditation API",
    description="Generate personalized meditation experiences based on your mood using OpenAI to find YouTube videos",
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

# Initialize the orchestrator - we'll reuse this instance
meditation_orchestrator = MeditationOrchestrator()

# Setup error handling for missing environment variables
@app.on_event("startup")
async def startup_db_client():
    from app.utils.db import init_supabase
    # Try to initialize Supabase but continue even if it fails
    try:
        init_supabase()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.info("Application will continue without database functionality")

class MeditationRequest(BaseModel):
    mood: str
    language: str = "english"  # Default to English if not specified

class FeedbackResponse(BaseModel):
    rating: int
    improved_mood: bool
    want_similar: bool
    improvement_suggestions: Optional[str] = None
    enjoyed_artist: Optional[bool] = None
    enjoyed_duration: Optional[bool] = None
    
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

# Helper function to get or create a user ID from cookies
async def get_user_id(user_id: Optional[str] = Cookie(None)):
    if not user_id:
        user_id = str(uuid.uuid4())
    return user_id

@app.post("/generate-meditation")
async def generate_meditation(request: MeditationRequest, user_id: str = Depends(get_user_id)):
    """
    Generate a personalized meditation based on the provided mood and language preference.
    
    The API will:
    1. Use OpenAI to find a suitable YouTube meditation video matching the mood (8-15 minutes long)
    2. Return the YouTube URL directly for the frontend to handle
    3. Store the URL in the database
    
    Returns JSON with YouTube URL and metadata.
    """
    try:
        # Find a meditation using our orchestrator
        youtube_url, source_info = await meditation_orchestrator.generate_meditation(
            request.mood, 
            language=request.language
        )
        
        # Check if feedback should be collected
        should_show_feedback = meditation_orchestrator.should_show_feedback_form(user_id)
        
        # Create response content
        response_content = {
            "status": "success",
            "mood": request.mood,
            "language": request.language,
            "message": f"Your {request.mood} meditation is ready to play.",
            "note": "Find a quiet place, sit comfortably, and breathe deeply as you watch the video.",
            "source_info": source_info,
            "should_show_feedback": should_show_feedback,
            "feedback_questions": meditation_orchestrator.get_feedback_questions() if should_show_feedback else [],
            "youtube_url": youtube_url  # Direct URL to the video
        }
        
        response = JSONResponse(content=response_content)
        
        # Set user_id cookie if it doesn't exist
        if not user_id:
            response.set_cookie(key="user_id", value=user_id)
            
        return response
    except Exception as e:
        # For debugging purposes, log the error
        logging.error(f"Error generating meditation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate meditation: {str(e)}")

@app.post("/submit-feedback")
async def submit_feedback(feedback: FeedbackResponse, user_id: str = Depends(get_user_id)):
    """
    Submit feedback about a meditation session.
    
    Args:
        feedback: The user's feedback responses
        user_id: The user identifier
        
    Returns:
        JSON response confirming the feedback was saved
    """
    try:
        # Convert feedback model to dictionary
        feedback_dict = feedback.dict()
        
        # Save the feedback
        success = await meditation_orchestrator.collect_feedback(user_id, feedback_dict)
        
        if success:
            return {
                "status": "success",
                "message": "Thank you for your feedback! We'll use it to improve your future meditation recommendations."
            }
        else:
            return {
                "status": "error",
                "message": "We couldn't save your feedback at this time. Please try again later."
            }
    except Exception as e:
        # For debugging purposes, log the error
        logging.error(f"Error saving feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

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