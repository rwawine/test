"""
Configuration module for the Telegram Bot
"""

import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    """Configuration class for the application"""
    
    # Bot configuration
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # Admin configuration
    ADMIN_IDS: List[int] = [
        int(admin_id.strip()) 
        for admin_id in os.getenv('ADMIN_IDS', '').split(',') 
        if admin_id.strip().isdigit()
    ]
    
    # Database configuration
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'data.duckdb')
    
    # Web admin configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    WEB_PORT: int = int(os.getenv('WEB_PORT', '5000'))
    WEB_HOST: str = os.getenv('WEB_HOST', '127.0.0.1')
    
    # File storage configuration
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
    EXPORT_FOLDER: str = os.getenv('EXPORT_FOLDER', 'exports')
    LOG_FOLDER: str = os.getenv('LOG_FOLDER', 'logs')
    
    # Lottery configuration
    MAX_PARTICIPANTS: int = int(os.getenv('MAX_PARTICIPANTS', '10000'))
    
    # File size limits (in bytes)
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB
    
    # Supported image formats
    ALLOWED_EXTENSIONS: set = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Phone validation
    PHONE_PATTERN: str = r'^(\+7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    
    # Loyalty card validation
    LOYALTY_CARD_PATTERN: str = r'^[0-9]{8,16}$'
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        
        if not cls.ADMIN_IDS:
            raise ValueError("At least one ADMIN_ID is required")
        
        return True