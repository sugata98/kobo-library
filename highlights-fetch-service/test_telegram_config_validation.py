#!/usr/bin/env python3
"""
Test Telegram configuration validation in Settings.

Tests that TELEGRAM_ENABLED=true requires all companion fields to be set.
"""

import os
import sys
from pydantic import ValidationError


def test_telegram_validation():
    """Test Telegram configuration validation."""
    
    print("=" * 70)
    print("Testing Telegram Configuration Validation")
    print("=" * 70)
    print()
    
    # Test 1: TELEGRAM_ENABLED=false (should not require fields)
    print("Test 1: TELEGRAM_ENABLED=false (should succeed)")
    print("-" * 70)
    
    os.environ.update({
        'B2_APPLICATION_KEY_ID': 'test_key_id',
        'B2_APPLICATION_KEY': 'test_key',
        'B2_BUCKET_NAME': 'test_bucket',
        'AUTH_USERNAME': 'test_user',
        'AUTH_PASSWORD': 'test_password',
        'JWT_SECRET_KEY': 'a' * 32,  # 32 chars minimum
        'TELEGRAM_ENABLED': 'false',
    })
    
    try:
        from app.core.config import Settings
        settings = Settings()
        print("✅ PASSED: Settings loaded successfully with TELEGRAM_ENABLED=false")
        print(f"   TELEGRAM_ENABLED: {settings.TELEGRAM_ENABLED}")
        print()
    except ValidationError as e:
        print(f"❌ FAILED: Unexpected validation error: {e}")
        print()
    
    # Test 2: TELEGRAM_ENABLED=true with missing fields (should fail)
    print("Test 2: TELEGRAM_ENABLED=true with missing fields (should fail)")
    print("-" * 70)
    
    os.environ['TELEGRAM_ENABLED'] = 'true'
    # Don't set TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_WEBHOOK_URL, etc.
    
    try:
        # Need to reimport to get fresh settings
        import importlib
        from app.core import config
        importlib.reload(config)
        
        print("❌ FAILED: Settings loaded but should have raised ValidationError")
        print()
    except ValidationError as e:
        error_msg = str(e)
        print("✅ PASSED: ValidationError raised as expected")
        print(f"   Error message: {error_msg[:200]}...")
        
        # Check that all required fields are mentioned
        required_fields = [
            'KOBO_API_KEY',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID',
            'TELEGRAM_WEBHOOK_URL',
            'GEMINI_API_KEY'
        ]
        
        missing_in_error = []
        for field in required_fields:
            if field in error_msg:
                print(f"   ✓ {field} mentioned in error")
            else:
                missing_in_error.append(field)
        
        if missing_in_error:
            print(f"   ⚠️  These fields not mentioned: {', '.join(missing_in_error)}")
        
        print()
    
    # Test 3: TELEGRAM_ENABLED=true with all fields set (should succeed)
    print("Test 3: TELEGRAM_ENABLED=true with all required fields (should succeed)")
    print("-" * 70)
    
    os.environ.update({
        'TELEGRAM_ENABLED': 'true',
        'KOBO_API_KEY': 'test_kobo_key',
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'TELEGRAM_CHAT_ID': '-1001234567890',
        'TELEGRAM_WEBHOOK_URL': 'https://example.com',
        'GEMINI_API_KEY': 'test_gemini_key',
    })
    
    try:
        import importlib
        from app.core import config
        importlib.reload(config)
        settings = config.settings
        
        print("✅ PASSED: Settings loaded successfully with all required fields")
        print(f"   TELEGRAM_ENABLED: {settings.TELEGRAM_ENABLED}")
        print(f"   TELEGRAM_BOT_TOKEN: {'***' if settings.TELEGRAM_BOT_TOKEN else 'None'}")
        print(f"   TELEGRAM_CHAT_ID: {settings.TELEGRAM_CHAT_ID}")
        print(f"   TELEGRAM_WEBHOOK_URL: {settings.TELEGRAM_WEBHOOK_URL}")
        print(f"   GEMINI_API_KEY: {'***' if settings.GEMINI_API_KEY else 'None'}")
        print()
    except ValidationError as e:
        print(f"❌ FAILED: Unexpected validation error: {e}")
        print()
    
    # Test 4: TELEGRAM_ENABLED=true with partial fields (should fail)
    print("Test 4: TELEGRAM_ENABLED=true with only some fields (should fail)")
    print("-" * 70)
    
    os.environ.update({
        'TELEGRAM_ENABLED': 'true',
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        # Missing: KOBO_API_KEY, TELEGRAM_CHAT_ID, TELEGRAM_WEBHOOK_URL, GEMINI_API_KEY
    })
    
    # Remove some fields
    for field in ['KOBO_API_KEY', 'TELEGRAM_CHAT_ID', 'TELEGRAM_WEBHOOK_URL', 'GEMINI_API_KEY']:
        os.environ.pop(field, None)
    
    try:
        import importlib
        from app.core import config
        importlib.reload(config)
        
        print("❌ FAILED: Settings loaded but should have raised ValidationError")
        print()
    except ValidationError as e:
        error_msg = str(e)
        print("✅ PASSED: ValidationError raised as expected")
        
        # Check which fields are mentioned
        expected_missing = ['KOBO_API_KEY', 'TELEGRAM_CHAT_ID', 'TELEGRAM_WEBHOOK_URL', 'GEMINI_API_KEY']
        found_fields = []
        
        for field in expected_missing:
            if field in error_msg:
                found_fields.append(field)
        
        print(f"   Missing fields in error: {', '.join(found_fields)}")
        print(f"   Expected {len(expected_missing)}, found {len(found_fields)}")
        
        if len(found_fields) == len(expected_missing):
            print("   ✓ All expected fields mentioned")
        else:
            print("   ⚠️  Some expected fields not mentioned")
        
        print()
    
    print("=" * 70)
    print("Testing Complete")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_telegram_validation()
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

