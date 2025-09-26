"""
Main entry point for the Telegram Lottery Bot
"""

import os
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import Config
from handlers import setup_handlers
from database.db_manager import DatabaseManager
from web.app import create_app
import threading

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_web_app():
    """Run Flask web application in a separate thread"""
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=False)

async def main():
    """Main function to start the bot"""
    # Initialize configuration
    config = Config()
    
    # Initialize database
    db_manager = DatabaseManager(config.DATABASE_PATH)
    db_manager.init_database()
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Setup handlers
    setup_handlers(dp, db_manager)
    
    # Start web application in a separate thread
    web_thread = threading.Thread(target=run_web_app, daemon=True)
    web_thread.start()
    
    logger.info("Starting Telegram Bot...")
    logger.info("Web admin panel available at: http://127.0.0.1:5000")
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())