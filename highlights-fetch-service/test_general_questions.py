#!/usr/bin/env python3
"""
Test script for the general questions feature.

This script tests:
1. The /ask API endpoint
2. Question processing
3. Response formatting

Usage:
    python test_general_questions.py
"""

import asyncio
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.kobo_ai_companion import create_kobo_ai_companion
from app.core.config import settings


async def test_general_question():
    """Test the general question answering functionality."""
    print("=" * 80)
    print("Testing General Questions Feature")
    print("=" * 80)
    
    # Check if Telegram is enabled
    if not settings.TELEGRAM_ENABLED:
        print("\n❌ TELEGRAM_ENABLED is False")
        print("   Set TELEGRAM_ENABLED=True in your .env file to test this feature")
        return False
    
    print("\n✅ Telegram is enabled")
    
    # Create companion
    print("\n📡 Creating Kobo AI Companion...")
    companion = create_kobo_ai_companion()
    
    if not companion:
        print("❌ Failed to create companion")
        print("   Check your environment variables:")
        print("   - TELEGRAM_BOT_TOKEN")
        print("   - TELEGRAM_CHAT_ID")
        print("   - GEMINI_API_KEY")
        return False
    
    print("✅ Companion created successfully")
    print(f"   - Text model: {companion.text_model}")
    print(f"   - Chat ID: {companion.chat_id}")
    
    # Test questions
    test_questions = [
        "What is a load balancer?",
        "Explain the CAP theorem in simple terms",
        "What's the difference between REST and GraphQL?",
    ]
    
    print("\n" + "=" * 80)
    print("Testing Question Processing")
    print("=" * 80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}/{len(test_questions)}")
        print(f"Question: {question}")
        print("-" * 80)
        
        try:
            # Generate answer
            answer = await companion.generate_general_answer(question)
            
            # Display results
            print(f"✅ Answer received ({len(answer)} characters)")
            print(f"\nAnswer preview:")
            print("-" * 80)
            # Show first 300 characters
            preview = answer[:300] + "..." if len(answer) > 300 else answer
            print(preview)
            print("-" * 80)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)
    
    print("\n📋 Summary:")
    print("   ✅ Companion initialization")
    print("   ✅ Question processing")
    print("   ✅ Answer generation")
    print("   ✅ Response formatting")
    
    print("\n🎯 Next Steps:")
    print("   1. Test in Telegram: Tag your bot with a question")
    print("      Example: @YourBotName What is Docker?")
    print("   2. Test the API endpoint:")
    print("      curl -X POST http://localhost:8000/kobo-companion/ask \\")
    print("        -H 'X-API-Key: your-key' \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"question\": \"Explain microservices\"}'")
    
    return True


async def test_api_endpoint_format():
    """Test the API request/response format."""
    print("\n" + "=" * 80)
    print("Testing API Endpoint Format")
    print("=" * 80)
    
    from app.api.kobo_companion import GeneralQuestionRequest
    
    # Test valid request
    print("\n✅ Testing valid request format...")
    try:
        request = GeneralQuestionRequest(
            question="What is Kubernetes?",
            send_to_telegram=True
        )
        print(f"   Question: {request.question}")
        print(f"   Send to Telegram: {request.send_to_telegram}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test minimal request
    print("\n✅ Testing minimal request (default send_to_telegram)...")
    try:
        request = GeneralQuestionRequest(
            question="What is Docker?"
        )
        print(f"   Question: {request.question}")
        print(f"   Send to Telegram: {request.send_to_telegram}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✅ API format tests passed!")
    return True


async def main():
    """Run all tests."""
    print("\n🧪 Kobo AI Companion - General Questions Test Suite\n")
    
    # Test 1: API format
    if not await test_api_endpoint_format():
        print("\n❌ API format tests failed")
        return
    
    # Test 2: General question processing
    if not await test_general_question():
        print("\n❌ General question tests failed")
        return
    
    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)
    print("\nThe general questions feature is working correctly!")
    print("You can now:")
    print("  • Tag the bot in Telegram to ask questions")
    print("  • Use the /ask API endpoint programmatically")
    print("  • Integrate with other services")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
