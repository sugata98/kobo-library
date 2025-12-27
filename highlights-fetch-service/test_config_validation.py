#!/usr/bin/env python3
"""
Test script to verify config validation works correctly.
Run this before deployment to ensure security requirements are enforced.
"""

import os
import sys
from pydantic import ValidationError

def test_jwt_secret_length():
    """Test that JWT_SECRET_KEY length validation works."""
    print("\n=== Testing JWT_SECRET_KEY Length Validation ===")
    
    # Save original env vars
    original_env = os.environ.copy()
    
    # Test 1: Short key (should fail)
    print("\n1. Testing short key (should fail)...")
    try:
        os.environ.update({
            'B2_APPLICATION_KEY_ID': 'test',
            'B2_APPLICATION_KEY': 'test',
            'B2_BUCKET_NAME': 'test',
            'AUTH_USERNAME': 'test',
            'AUTH_PASSWORD': 'test',
            'JWT_SECRET_KEY': 'tooshort',  # Only 8 characters
        })
        
        # Force reload of settings
        import importlib
        from app.core import config
        importlib.reload(config)
        
        print("   ❌ FAILED: Should have raised ValidationError")
        return False
        
    except ValidationError as e:
        print(f"   ✅ PASSED: Correctly rejected short key")
        print(f"   Error: {e.errors()[0]['msg']}")
    
    # Test 2: Valid key (should pass)
    print("\n2. Testing valid key (should pass)...")
    try:
        import secrets
        valid_key = secrets.token_urlsafe(32)  # 43+ characters
        
        os.environ['JWT_SECRET_KEY'] = valid_key
        
        # Force reload
        importlib.reload(config)
        
        print(f"   ✅ PASSED: Accepted valid key (length: {len(valid_key)})")
        
    except ValidationError as e:
        print(f"   ❌ FAILED: Should have accepted valid key")
        print(f"   Error: {e}")
        return False
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    
    return True

def test_token_expiry():
    """Test that token expiry validation works."""
    print("\n=== Testing JWT_ACCESS_TOKEN_EXPIRE_MINUTES Validation ===")
    
    # Save original env vars
    original_env = os.environ.copy()
    
    # Test 1: Excessive expiry (should fail)
    print("\n1. Testing excessive expiry (should fail)...")
    try:
        import secrets
        os.environ.update({
            'B2_APPLICATION_KEY_ID': 'test',
            'B2_APPLICATION_KEY': 'test',
            'B2_BUCKET_NAME': 'test',
            'AUTH_USERNAME': 'test',
            'AUTH_PASSWORD': 'test',
            'JWT_SECRET_KEY': secrets.token_urlsafe(32),
            'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': '50000',  # More than 30 days
        })
        
        # Force reload
        import importlib
        from app.core import config
        importlib.reload(config)
        
        print("   ❌ FAILED: Should have raised ValidationError")
        return False
        
    except ValidationError as e:
        print(f"   ✅ PASSED: Correctly rejected excessive expiry")
        print(f"   Error: {e.errors()[0]['msg']}")
    
    # Test 2: Valid expiry (should pass)
    print("\n2. Testing valid expiry (should pass)...")
    try:
        os.environ['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = '43200'  # 30 days
        
        # Force reload
        importlib.reload(config)
        
        print(f"   ✅ PASSED: Accepted valid expiry (43200 minutes = 30 days)")
        
    except ValidationError as e:
        print(f"   ❌ FAILED: Should have accepted valid expiry")
        print(f"   Error: {e}")
        return False
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    
    return True

def test_secret_str_protection():
    """Test that SecretStr properly hides secrets."""
    print("\n=== Testing SecretStr Protection ===")
    
    # Save original env vars
    original_env = os.environ.copy()
    
    try:
        import secrets
        secret_key = secrets.token_urlsafe(32)
        
        os.environ.update({
            'B2_APPLICATION_KEY_ID': 'test',
            'B2_APPLICATION_KEY': 'test_b2_key',
            'B2_BUCKET_NAME': 'test',
            'AUTH_USERNAME': 'test_user',
            'AUTH_PASSWORD': 'test_password',
            'JWT_SECRET_KEY': secret_key,
        })
        
        # Force reload
        import importlib
        from app.core import config
        importlib.reload(config)
        
        # Check that secrets are masked in string representation
        settings_str = str(config.settings)
        
        # These should NOT appear in plain text
        if 'test_b2_key' in settings_str:
            print("   ❌ FAILED: B2_APPLICATION_KEY visible in settings string")
            return False
        
        if 'test_password' in settings_str:
            print("   ❌ FAILED: AUTH_PASSWORD visible in settings string")
            return False
        
        if secret_key in settings_str:
            print("   ❌ FAILED: JWT_SECRET_KEY visible in settings string")
            return False
        
        # Verify we can still access secrets with get_secret_value()
        if config.settings.AUTH_USERNAME.get_secret_value() != 'test_user':
            print("   ❌ FAILED: Cannot access AUTH_USERNAME with get_secret_value()")
            return False
        
        print("   ✅ PASSED: Secrets properly masked in string representation")
        print("   ✅ PASSED: Secrets accessible via get_secret_value()")
        
    except Exception as e:
        print(f"   ❌ FAILED: Unexpected error: {e}")
        return False
    
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
    
    return True

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("CONFIG VALIDATION TEST SUITE")
    print("=" * 60)
    
    results = []
    
    results.append(("JWT Secret Length", test_jwt_secret_length()))
    results.append(("Token Expiry", test_token_expiry()))
    results.append(("SecretStr Protection", test_secret_str_protection()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! Config validation is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

