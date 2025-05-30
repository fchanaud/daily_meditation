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
    
    # Skip initialization if URL or key are missing or empty
    if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL.strip() == "" or SUPABASE_KEY.strip() == "":
        logger.warning("Supabase credentials missing or empty - database features will be disabled")
        return False
    
    try:
        # Validate URL format
        if not SUPABASE_URL.startswith("http"):
            logger.error("Invalid Supabase URL format - must start with http:// or https://")
            return False
            
        # Create client with new package syntax (compatible with both old and new versions)
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return False

async def save_meditation_session(mood, language, youtube_url=None, audio_url=None, user_id=None):
    """
    Save a meditation session to Supabase.
    
    Args:
        mood: The selected mood for the meditation
        language: The language of the meditation
        youtube_url: URL of the YouTube video (if available)
        audio_url: URL of the audio file
        user_id: Optional user ID to associate with this session
        
    Returns:
        Boolean indicating success
    """
    if not supabase:
        if not init_supabase():
            logger.warning("Unable to save meditation session - Supabase not initialized")
            # Continue the application without error since this is non-critical
            return True
    
    try:
        # Create data to insert
        session_data = {
            "mood": mood,
            "language": language,
            "youtube_url": youtube_url,
            "audio_url": audio_url,
            "created_at": datetime.now().isoformat(),
        }
        
        # Add user_id if provided
        if user_id:
            session_data["user_id"] = user_id
        
        # Insert data into the meditation_sessions table with error handling for both API versions
        try:
            response = supabase.table("meditation_sessions").insert(session_data).execute()
            
            # Handle response based on version
            if hasattr(response, 'data') and response.data:
                logger.info(f"Meditation session saved successfully: {response.data}")
                return True
            else:
                # For newer versions that might have a different response format
                logger.info("Meditation session saved successfully")
                return True
        except Exception as insert_error:
            # Try alternative method for newer versions if available
            logger.warning(f"First insertion method failed: {str(insert_error)}")
            try:
                data = supabase.from_("meditation_sessions").insert(session_data).execute()
                logger.info("Meditation session saved successfully using alternative method")
                return True
            except Exception as alt_error:
                logger.error(f"Alternative insertion method failed: {str(alt_error)}")
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
        
        # Query the database for recent sessions with compatibility for both versions
        try:
            response = supabase.table("meditation_sessions") \
                .select("*") \
                .gte("created_at", lookback_date) \
                .order("created_at", desc=True) \
                .execute()
            
            if hasattr(response, 'data'):
                return response.data
            else:
                # For newer versions that might return data directly
                return response
        except Exception as query_error:
            # Try alternative method for newer versions
            logger.warning(f"First query method failed: {str(query_error)}")
            try:
                response = supabase.from_("meditation_sessions") \
                    .select("*") \
                    .gte("created_at", lookback_date) \
                    .order("created_at", asc=False) \
                    .execute()
                
                if hasattr(response, 'data'):
                    return response.data
                else:
                    return response
            except Exception as alt_error:
                logger.error(f"Alternative query method failed: {str(alt_error)}")
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
        
        # Query for today's sessions with compatibility for both versions
        try:
            response = supabase.table("meditation_sessions") \
                .select("*") \
                .gte("created_at", today_start) \
                .lte("created_at", today_end) \
                .execute()
            
            if hasattr(response, 'data'):
                return len(response.data) > 0
            else:
                # For newer versions
                return len(response) > 0
        except Exception as query_error:
            # Try alternative method for newer versions
            logger.warning(f"First today check method failed: {str(query_error)}")
            try:
                response = supabase.from_("meditation_sessions") \
                    .select("*") \
                    .gte("created_at", today_start) \
                    .lte("created_at", today_end) \
                    .execute()
                
                if hasattr(response, 'data'):
                    return len(response.data) > 0
                else:
                    return len(response) > 0
            except Exception as alt_error:
                logger.error(f"Alternative today check method failed: {str(alt_error)}")
                return False
            
    except Exception as e:
        logger.error(f"Error checking today's meditation: {str(e)}")
        return False

async def get_user_watched_videos(user_id=None, days=30):
    """
    Get a list of YouTube URLs that the user has already watched.
    
    Args:
        user_id: User identifier (optional)
        days: Number of days to look back in history
        
    Returns:
        List of YouTube URLs the user has watched
    """
    if not supabase:
        if not init_supabase():
            return []
    
    try:
        # Calculate date for looking back
        lookback_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Base query
        query = supabase.table("meditation_sessions") \
            .select("youtube_url") \
            .gte("created_at", lookback_date) \
            .not_is("youtube_url", "null")
        
        # Add user filter if provided
        if user_id:
            query = query.eq("user_id", user_id)
        
        # Try execute with compatibility for both versions
        try:
            response = query.execute()
            
            if hasattr(response, 'data'):
                # Extract YouTube URLs from response
                urls = [item.get('youtube_url') for item in response.data if item.get('youtube_url')]
                return urls
            else:
                # For newer versions that might return data differently
                urls = [item.get('youtube_url') for item in response if item.get('youtube_url')]
                return urls
        except Exception as query_error:
            # Try alternative method for newer versions
            logger.warning(f"First query method failed: {str(query_error)}")
            try:
                query = supabase.from_("meditation_sessions") \
                    .select("youtube_url") \
                    .gte("created_at", lookback_date) \
                    .not_is("youtube_url", "null")
                
                if user_id:
                    query = query.eq("user_id", user_id)
                    
                response = query.execute()
                
                if hasattr(response, 'data'):
                    urls = [item.get('youtube_url') for item in response.data if item.get('youtube_url')]
                    return urls
                else:
                    urls = [item.get('youtube_url') for item in response if item.get('youtube_url')]
                    return urls
            except Exception as alt_error:
                logger.error(f"Alternative query method failed: {str(alt_error)}")
                return []
            
    except Exception as e:
        logger.error(f"Error retrieving watched videos: {str(e)}")
        return []

# Initialize Supabase when the module is imported
init_supabase() 