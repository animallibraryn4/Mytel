import asyncio
import logging
import threading
import time
from pyrogram import Client, idle
from config import config
from database import db
from plugins.anime_handler import AnimeHandler


#Ye check karega ki mkvmerge installed hai ya nahi
if os.system("mkvmerge --version") != 0:
    print("mkvtoolnix nahi mila, install kar raha hoon...")
    os.system("apt-get update && apt-get install python3-libtorrent")
else:
    print("libtorrent pehle se installed hai.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE)
    ]
)
logger = logging.getLogger('AutoAnimeBot')

class AutoAnimeBot:
    def __init__(self):
        self.bot = None
        self.file_client = None
        self.bot_me = None
        self.anime_handler = None
        
    async def initialize_clients(self):
        """Initialize Telegram clients"""
        # File bot client
        self.file_client = Client(
            "FileBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.CLIENT_BOT_TOKEN,
            plugins={"root": "plugins"}
        )
        
        # Main bot client
        self.bot = Client(
            "mainbot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.MAIN_BOT_TOKEN,
            plugins={"root": "plugins"}
        )
        
        # Initialize anime handler
        self.anime_handler = AnimeHandler(self.bot, self.file_client)
        
    def start_background_tasks(self):
        """Start background tasks for checking and processing anime"""
        # Check for new anime periodically
        threading.Thread(
            target=self._interval_task,
            args=(self.anime_handler.check_new_anime, config.ANIME_CHECK_INTERVAL),
            daemon=True
        ).start()
        
        # Process anime queue periodically
        threading.Thread(
            target=self._interval_task,
            args=(self.anime_handler.process_anime_queue, config.WORKER_CHECK_INTERVAL),
            daemon=True
        ).start()
        
        logger.info("Background tasks started")
    
    def _interval_task(self, callback, interval):
        """Run a callback at regular intervals"""
        while True:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in interval task: {e}")
            time.sleep(interval)
    
    async def start(self):
        """Start the bot"""
        logger.info(f"AutoAnimeBot starting...")
        logger.info(f"Author: {config.AUTHOR}")
        logger.info(f"License: {config.LICENSED_UNDER}")
        
        # Test database connection
        if not db.test_connection():
            logger.critical("Database connection failed. Exiting.")
            return
        
        # Initialize clients
        await self.initialize_clients()
        
        # Start clients
        await self.file_client.start()
        await self.bot.start()
        
        # Get bot info
        self.bot_me = await self.bot.get_me()
        logger.info(f"Main bot started: @{self.bot_me.username}")
        
        # Set bot_me in anime handler
        self.anime_handler.bot_me = self.bot_me
        
        # Send startup notifications
        await self.send_startup_notifications()
        
        # Start background tasks
        self.start_background_tasks()
        
        # Keep bot running
        logger.info("Bot is now running...")
        await idle()
        
        # Stop clients
        await self.stop()
    
    async def send_startup_notifications(self):
        """Send startup notifications to production chat"""
        try:
            await self.bot.send_message(
                config.PRODUCTION_CHAT,
                "✅ Main Bot Started Successfully"
            )
            await self.file_client.send_message(
                config.PRODUCTION_CHAT,
                "✅ File Bot Started Successfully"
            )
        except Exception as e:
            logger.error(f"Failed to send startup notifications: {e}")
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping bot...")
        if self.file_client:
            await self.file_client.stop()
        if self.bot:
            await self.bot.stop()
        logger.info("Bot stopped")

async def main():
    """Main function"""
    bot = AutoAnimeBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")

if __name__ == "__main__":
    # Create downloads directory if it doesn't exist
    import os
    os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)
    
    # Run the bot
    asyncio.run(main())

