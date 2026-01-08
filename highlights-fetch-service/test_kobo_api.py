#!/usr/bin/env python3
"""
Test script for Kobo AI Companion API

Tests the /kobo-ask endpoint with sample data.
"""

import requests
import json
import sys
from typing import Dict, Any


def test_kobo_ask(api_url: str, api_key: str, test_data: Dict[str, Any]) -> bool:
    """
    Test sending a question/highlight to the API.
    
    Args:
        api_url: The API endpoint URL
        api_key: The API key for authentication
        test_data: The test request data
        
    Returns:
        True if successful, False otherwise
    """
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    book = test_data['context']['book']
    author = test_data['context']['author']
    
    print(f"Testing API: {api_url}")
    print(f"Question from '{book}' by {author}")
    print(f"Text: {test_data['text'][:60]}...")
    print("-" * 60)
    
    try:
        response = requests.post(
            api_url,
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Response is plain text (for Kobo dialog)
            explanation = response.text
            print(f"✅ Success!")
            print(f"Response (plain text):")
            print("-" * 60)
            print(explanation[:500])  # Show first 500 chars
            if len(explanation) > 500:
                print("...")
                print(f"(Total length: {len(explanation)} characters)")
            print("-" * 60)
            print(f"💬 Full analysis sent to Telegram in background")
            return True
        else:
            print(f"❌ Failed!")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Kobo AI Companion API Test (/kobo-ask)")
    print("=" * 60)
    print()
    
    # Configuration (update these values)
    API_URL = "http://localhost:8000/kobo-ask"  # Change for production: https://api.readr.space/kobo-ask
    API_KEY = "your-api-key-here"  # Update with your actual API key
    
    # Test data (matches Kobo script format)
    test_cases = [
        {
            "mode": "explain",
            "text": "Load balancers distribute incoming traffic across multiple backend servers to ensure high availability and fault tolerance.",
            "context": {
                "book": "System Design Interview",
                "author": "Alex Xu",
                "chapter": "Chapter 2: Scalability",
                "device_id": "test-device"
            }
        },
        {
            "mode": "explain",
            "text": "A binary search tree maintains the property that all left children are smaller than the parent node, and all right children are larger.",
            "context": {
                "book": "Introduction to Algorithms",
                "author": "CLRS",
                "chapter": "Chapter 12: Binary Search Trees",
                "device_id": "test-device"
            }
        },
        {
            "mode": "explain",
            "text": "Microservices architecture allows teams to develop, deploy, and scale services independently, but introduces complexity in inter-service communication.",
            "context": {
                "book": "Building Microservices",
                "author": "Sam Newman",
                "chapter": None,  # Test without chapter
                "device_id": "test-device"
            }
        }
    ]
    
    # Check if API key is configured
    if API_KEY == "your-api-key-here":
        print("⚠️  Warning: Using default API key!")
        print("Please update API_KEY in this script with your actual key.")
        print()
        
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Exiting...")
            sys.exit(0)
        print()
    
    # Run tests
    results = []
    for i, test_data in enumerate(test_cases, 1):
        print(f"Test Case #{i}")
        print("=" * 60)
        
        # Remove None chapter if present
        if test_data['context'].get("chapter") is None:
            test_data_clean = test_data.copy()
            test_data_clean['context'] = {k: v for k, v in test_data['context'].items() if k != "chapter" or v is not None}
        else:
            test_data_clean = test_data
        
        success = test_kobo_ask(API_URL, API_KEY, test_data_clean)
        results.append(success)
        
        print()
        
        if i < len(test_cases):
            input("Press Enter to continue to next test...")
            print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    print()
    
    if all(results):
        print("🎉 All tests passed!")
        print()
        print("Next steps:")
        print("1. Check Telegram for the full analysis messages")
        print("2. Verify that images were generated (if applicable)")
        print("3. Try replying to the bot in Telegram to test conversation mode")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
