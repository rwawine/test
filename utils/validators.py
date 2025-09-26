"""
Validation utilities for user input
"""

import re
from config import Config

def validate_name(name: str) -> bool:
    """Validate full name"""
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # Check length
    if len(name) < 2 or len(name) > 50:
        return False
    
    # Check if contains only letters, spaces, and common name characters
    pattern = r'^[a-zA-Zа-яА-ЯёЁ\s\-\.]+$'
    
    return bool(re.match(pattern, name))

def validate_phone(phone: str) -> bool:
    """Validate Russian phone number"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all spaces and dashes
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Russian phone patterns
    patterns = [
        r'^\+7[0-9]{10}$',  # +7XXXXXXXXXX
        r'^8[0-9]{10}$',    # 8XXXXXXXXXX
        r'^7[0-9]{10}$'     # 7XXXXXXXXXX
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    
    return False

def validate_loyalty_card(card: str) -> bool:
    """Validate loyalty card number"""
    if not card or not isinstance(card, str):
        return False
    
    card = card.strip()
    
    # Check if contains only digits
    if not card.isdigit():
        return False
    
    # Check length (8-16 digits)
    if len(card) < 8 or len(card) > 16:
        return False
    
    return True

def normalize_phone(phone: str) -> str:
    """Normalize phone number to +7XXXXXXXXXX format"""
    if not phone:
        return ""
    
    # Remove all non-digits except +
    phone = re.sub(r'[^\d\+]', '', phone)
    
    if phone.startswith('+7'):
        return phone
    elif phone.startswith('8') and len(phone) == 11:
        return '+7' + phone[1:]
    elif phone.startswith('7') and len(phone) == 11:
        return '+' + phone
    elif len(phone) == 10:
        return '+7' + phone
    
    return phone