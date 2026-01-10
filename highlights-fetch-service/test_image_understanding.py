"""
Test script for Image Understanding feature

Tests the Telegram bot's ability to analyze images and answer questions about them.

Usage:
    python test_image_understanding.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.kobo_ai_companion import create_kobo_ai_companion
from app.core.config import settings


async def test_image_understanding():
    """Test the image understanding capability"""
    
    print("=" * 70)
    print("Image Understanding Feature Test")
    print("=" * 70)
    print()
    
    # Check if companion is configured
    if not settings.TELEGRAM_ENABLED:
        print("❌ TELEGRAM_ENABLED is False. Please enable it in your .env file.")
        return
    
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not configured. Please set it in your .env file.")
        return
    
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not configured. Please set it in your .env file.")
        return
    
    print("✅ Configuration looks good!")
    print()
    
    # Create companion
    print("Creating Kobo AI Companion...")
    companion = create_kobo_ai_companion()
    
    if not companion:
        print("❌ Failed to create companion service.")
        return
    
    print("✅ Companion service created successfully!")
    print()
    
    # Display capabilities
    print("🎯 Image Understanding Capabilities:")
    print()
    print("1. Via Telegram:")
    print("   - Send an image with a caption mentioning your bot")
    print("   - Example: @your_bot_username What's in this diagram?")
    print()
    print("2. Via API:")
    print("   - POST /api/ask-with-image")
    print("   - Upload image file + question")
    print("   - Requires X-API-Key header")
    print()
    
    # Test with a simple example (if you want to test programmatically)
    print("📝 Testing image analysis (simulated)...")
    print()
    
    # Create a simple test image (1x1 red pixel PNG)
    import base64
    
    # Minimal 1x1 red pixel PNG (base64 encoded)
    test_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    test_image_bytes = base64.b64decode(test_png_b64)
    
    question = "This is a test image. Just acknowledge that you can see it."
    
    try:
        print(f"Question: {question}")
        print(f"Image: Test PNG ({len(test_image_bytes)} bytes)")
        print()
        print("Generating analysis...")
        
        response = await companion.generate_image_analysis(question, test_image_bytes)
        
        print()
        print("✅ Analysis generated successfully!")
        print()
        print("Response:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        print()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print()
    print("💡 How to use:")
    print()
    print("1. In Telegram:")
    print("   - Send any image to your configured chat/group")
    print("   - Add a caption with your bot's @username and a question")
    print("   - Example: '@mybotname What does this diagram show?'")
    print()
    print("2. Via API (curl example):")
    print("   curl -X POST http://localhost:8000/api/ask-with-image \\")
    print("     -H 'X-API-Key: YOUR_API_KEY' \\")
    print("     -F 'image=@path/to/image.jpg' \\")
    print("     -F 'question=What is in this image?' \\")
    print("     -F 'send_to_telegram=true'")
    print()
    print("3. Supported formats:")
    print("   - JPEG, PNG, GIF, WebP")
    print("   - Max size: 20MB")
    print()
    print("4. The bot can analyze:")
    print("   - Technical diagrams and architecture drawings")
    print("   - Code screenshots")
    print("   - Charts and graphs")
    print("   - Documents and text in images")
    print("   - Photos and general images")
    print()


if __name__ == "__main__":
    asyncio.run(test_image_understanding())
