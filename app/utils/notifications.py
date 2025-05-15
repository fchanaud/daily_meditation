import os
import logging
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pushover credentials
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

async def send_pushover_notification(title, message, priority=0):
    """
    Send a notification via Pushover.
    
    Args:
        title: The notification title
        message: The notification message
        priority: The priority level (-2 to 2)
        
    Returns:
        Boolean indicating success
    """
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        logger.warning("Pushover credentials not found in environment variables")
        return False
    
    try:
        # Create the notification payload
        payload = {
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message,
            "priority": priority,
        }
        
        # Send the notification
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.pushover.net/1/messages.json", data=payload)
            
        if response.status_code == 200:
            logger.info(f"Pushover notification sent successfully: {title}")
            return True
        else:
            logger.error(f"Failed to send Pushover notification: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Pushover notification: {str(e)}")
        return False

async def send_meditation_reminder():
    """
    Send a reminder to meditate.
    
    Returns:
        Boolean indicating success
    """
    title = "Meditation Reminder"
    message = "You haven't meditated today. Take 10 minutes to find your calm and peace."
    
    return await send_pushover_notification(title, message, priority=1) 