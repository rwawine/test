"""
File handling utilities
"""

import os
import uuid
import aiofiles
import logging
from pathlib import Path
from datetime import datetime
from aiogram import Bot
from typing import Optional

logger = logging.getLogger(__name__)

async def save_photo(bot: Bot, file_id: str, user_id: int) -> Optional[str]:
    """Save photo from Telegram and return local path"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Get file info
        file_info = await bot.get_file(file_id)
        
        # Generate unique filename
        file_extension = Path(file_info.file_path).suffix or '.jpg'
        filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}{file_extension}"
        local_path = upload_dir / filename
        
        # Download file
        await bot.download_file(file_info.file_path, local_path)
        
        logger.info(f"Photo saved: {local_path}")
        return str(local_path)
        
    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        return None

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def is_allowed_file_type(filename: str) -> bool:
    """Check if file type is allowed"""
    from config import Config
    
    if not filename:
        return False
    
    extension = Path(filename).suffix.lower().lstrip('.')
    return extension in Config.ALLOWED_EXTENSIONS

def clean_old_files(directory: str, days_old: int = 30) -> int:
    """Clean files older than specified days"""
    cleaned_count = 0
    
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            return 0
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        for file_path in directory_path.iterdir():
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
                    
    except Exception as e:
        logger.error(f"Error cleaning old files: {e}")
    
    return cleaned_count