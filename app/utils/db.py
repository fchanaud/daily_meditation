import os
import logging
from datetime import datetime, timedelta
from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize the Supabase client
supabase: Client = None

def init_supabase():
    """Initialize the Supabase client if credentials are available."""
    global supabase
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase credentials not found in environment variables")
        return False
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return False

async def save_meditation_session(mood, language, youtube_url=None, audio_url=None):
    """
    Save a meditation session to Supabase.
    
    Args:
        mood: The selected mood for the meditation
        language: The language of the meditation
        youtube_url: URL of the YouTube video (if available)
        audio_url: URL of the audio file
        
    Returns:
        Boolean indicating success
    """
    if not supabase:
        if not init_supabase():
            logger.warning("Unable to save meditation session - Supabase not initialized")
            return False
    
    try:
        # Create data to insert
        session_data = {
            "mood": mood,
            "language": language,
            "youtube_url": youtube_url,
            "audio_url": audio_url,
            "created_at": datetime.now().isoformat(),
        }
        
        # Insert data into the meditation_sessions table
        response = supabase.table("meditation_sessions").insert(session_data).execute()
        
        if hasattr(response, 'data') and response.data:
            logger.info(f"Meditation session saved successfully: {response.data}")
            return True
        else:
            logger.error(f"Failed to save meditation session: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving meditation session: {str(e)}")
        return False

async def get_recent_meditations(days=5):
    """
    Get recent meditation sessions from the database.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of meditation sessions
    """
    if not supabase:
        if not init_supabase():
            return []
    
    try:
        # Calculate date for looking back
        lookback_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Query the database for recent sessions
        response = supabase.table("meditation_sessions") \
            .select("*") \
            .gte("created_at", lookback_date) \
            .order("created_at", desc=True) \
            .execute()
        
        if hasattr(response, 'data'):
            return response.data
        else:
            logger.error(f"Failed to get recent meditation sessions: {response}")
            return []
            
    except Exception as e:
        logger.error(f"Error retrieving recent meditation sessions: {str(e)}")
        return []

async def check_meditation_today():
    """
    Check if a meditation session has been recorded today.
    
    Returns:
        Boolean indicating if a meditation has been done today
    """
    if not supabase:
        if not init_supabase():
            return False
    
    try:
        # Get today's date bounds
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        
        # Query for today's sessions
        response = supabase.table("meditation_sessions") \
            .select("*") \
            .gte("created_at", today_start) \
            .lte("created_at", today_end) \
            .execute()
        
        if hasattr(response, 'data'):
            return len(response.data) > 0
        else:
            logger.error(f"Failed to check today's meditation: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking today's meditation: {str(e)}")
        return False

# Initialize Supabase when the module is imported
init_supabase() 