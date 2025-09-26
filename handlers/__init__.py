"""
Main handlers setup module
"""

from aiogram import Dispatcher
from .registration import create_registration_router
from .status import create_status_router
from .support import create_support_router

def setup_handlers(dp, db_manager):
    """Setup all handlers"""
    
    # Include routers
    dp.include_router(create_registration_router(db_manager))
    dp.include_router(create_status_router(db_manager))
    dp.include_router(create_support_router(db_manager))