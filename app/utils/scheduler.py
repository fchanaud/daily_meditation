import asyncio
import logging
import schedule
import time
import datetime
from threading import Thread
from app.utils.db import check_meditation_today
from app.utils.notifications import send_meditation_reminder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flag to track if the scheduler is running
is_running = False

async def check_and_remind():
    """
    Check if a meditation has been done today and send a reminder if not.
    """
    logger.info("Running daily meditation check...")
    
    # Check if it's afternoon (after 2pm)
    now = datetime.datetime.now()
    if now.hour < 14:  # Before 2pm
        logger.info("Skipping reminder check - it's before 2pm")
        return
    
    # Check if meditation has been done today
    meditated_today = await check_meditation_today()
    
    if not meditated_today:
        logger.info("No meditation recorded today - sending reminder")
        await send_meditation_reminder()
    else:
        logger.info("Meditation already done today - no reminder needed")

def run_scheduler_thread():
    """
    Run the scheduler in a separate thread.
    """
    global is_running
    
    if is_running:
        logger.warning("Scheduler already running")
        return
    
    try:
        is_running = True
        
        # Schedule the afternoon check
        schedule.every().day.at("14:00").do(lambda: asyncio.run(check_and_remind()))
        
        # Also schedule a backup check later in the day
        schedule.every().day.at("18:00").do(lambda: asyncio.run(check_and_remind()))
        
        logger.info("Meditation reminder scheduler started")
        
        # Run the scheduling loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except Exception as e:
        logger.error(f"Error in scheduler thread: {str(e)}")
    finally:
        is_running = False

def start_scheduler():
    """
    Start the scheduler in a background thread.
    """
    scheduler_thread = Thread(target=run_scheduler_thread, daemon=True)
    scheduler_thread.start()
    logger.info("Meditation reminder scheduler thread started")
    return scheduler_thread

# Start the scheduler when the module is imported
scheduler_thread = None

def init_scheduler():
    """Initialize the scheduler if not already running."""
    global scheduler_thread
    
    if scheduler_thread is None or not scheduler_thread.is_alive():
        scheduler_thread = start_scheduler()
        return True
    return False 