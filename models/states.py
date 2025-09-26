"""
FSM States for user registration process
"""

from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """States for participant registration process"""
    WAITING_NAME = State()
    WAITING_PHONE = State()
    WAITING_LOYALTY_CARD = State()
    WAITING_LEAFLET_PHOTO = State()
    CONFIRMATION = State()
    REGISTRATION_COMPLETE = State()

class SupportStates(StatesGroup):
    """States for support ticket creation"""
    WAITING_CATEGORY = State()
    WAITING_DESCRIPTION = State()
    WAITING_ATTACHMENT = State()
    CONFIRMATION = State()