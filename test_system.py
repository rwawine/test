"""
Test script to verify basic functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all main imports work"""
    try:
        print("Testing imports...")
        
        from config import Config
        print("✓ Config imported")
        
        from database.db_manager import DatabaseManager
        print("✓ DatabaseManager imported")
        
        from utils.validators import validate_phone, validate_name, validate_loyalty_card
        print("✓ Validators imported")
        
        from utils.lottery import LotterySystem
        print("✓ LotterySystem imported")
        
        from keyboards.reply_keyboards import get_main_menu_keyboard
        print("✓ Keyboards imported")
        
        from models.states import RegistrationStates
        print("✓ States imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database initialization"""
    try:
        print("\nTesting database...")
        
        from database.db_manager import DatabaseManager
        
        # Test with in-memory database
        db = DatabaseManager(":memory:")
        db.init_database()
        
        # Test basic operations
        stats = db.get_statistics()
        print(f"✓ Database initialized. Total participants: {stats['total_participants']}")
        
        # Test participant operations
        participant_id = db.add_participant(
            telegram_id=123456789,
            username="testuser",
            full_name="Test User",
            phone_number="+79123456789",
            loyalty_card="12345678",
            leaflet_photo_path="test.jpg"
        )
        
        participant = db.get_participant_by_telegram_id(123456789)
        assert participant is not None
        assert participant['full_name'] == "Test User"
        
        print("✓ Database operations working")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_validators():
    """Test validation functions"""
    try:
        print("\nTesting validators...")
        
        from utils.validators import validate_phone, validate_name, validate_loyalty_card
        
        # Test phone validation
        assert validate_phone("+79123456789") == True
        assert validate_phone("invalid") == False
        print("✓ Phone validation working")
        
        # Test name validation
        assert validate_name("John Doe") == True
        assert validate_name("") == False
        assert validate_name("A" * 100) == False
        print("✓ Name validation working")
        
        # Test loyalty card validation
        assert validate_loyalty_card("12345678") == True
        assert validate_loyalty_card("123") == False
        assert validate_loyalty_card("abc") == False
        print("✓ Loyalty card validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Validator error: {e}")
        return False

def test_lottery():
    """Test lottery system"""
    try:
        print("\nTesting lottery system...")
        
        from database.db_manager import DatabaseManager
        from utils.lottery import LotterySystem
        
        # Create test database
        db = DatabaseManager(":memory:")
        db.init_database()
        
        # Add test participants
        for i in range(5):
            participant_id = db.add_participant(
                telegram_id=100000000 + i,
                username=f"user{i}",
                full_name=f"User {i}",
                phone_number=f"+7912345678{i}",
                loyalty_card=f"1234567{i}",
                leaflet_photo_path=f"test{i}.jpg"
            )
            # Approve participant
            db.update_participant_status(participant_id, "approved", 123456789)
        
        # Test lottery
        lottery = LotterySystem(db)
        eligible = lottery.get_eligible_participants()
        print(f"✓ Found {len(eligible)} eligible participants")
        
        # Generate seed
        seed, seed_hash = lottery.generate_seed()
        print(f"✓ Generated seed hash: {seed_hash[:16]}...")
        
        # Test deterministic random
        random_num = lottery.deterministic_random(seed, 100, 0)
        print(f"✓ Deterministic random: {random_num}")
        
        print("✓ Lottery system working")
        return True
        
    except Exception as e:
        print(f"❌ Lottery error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting system tests...\n")
    
    tests = [
        test_imports,
        test_database,
        test_validators,
        test_lottery
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)