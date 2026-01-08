#!/usr/bin/env python3
"""
Test script for Kobo AI Companion API

Tests the /kobo-highlight endpoint with sample data.
"""

import requests
import json
import sys
from typing import Dict, Any


def test_highlight(api_url: str, api_key: str, test_data: Dict[str, Any]) -> bool:
    """
    Test sending a highlight to the API.
    
    Args:
        api_url: The API endpoint URL
        api_key: The API key for authentication
        test_data: The test highlight data
        
    Returns:
        True if successful, False otherwise
    """
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"Testing API: {api_url}")
    print(f"Sending highlight from '{test_data['book']}' by {test_data['author']}")
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
            result = response.json()
            print(f"✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
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
    print("Kobo AI Companion API Test")
    print("=" * 60)
    print()
    
    # Configuration (update these values)
    API_URL = "http://localhost:8000/kobo-highlight"  # Change for production
    API_KEY = "your-api-key-here"  # Update with your actual API key
    
    # Test data
    test_cases = [
        {
            "text": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
            "book": "Pride and Prejudice",
            "author": "Jane Austen",
            "chapter": "Chapter 1"
        },
        {
            "text": "War is peace. Freedom is slavery. Ignorance is strength.",
            "book": "1984",
            "author": "George Orwell",
            "chapter": None  # Test without chapter
        },
        {
            "text": "I must not fear. Fear is the mind-killer. Fear is the little-death that brings total obliteration.",
            "book": "Dune",
            "author": "Frank Herbert",
            "chapter": "Book One: Dune"
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
        if test_data.get("chapter") is None:
            test_data_clean = {k: v for k, v in test_data.items() if k != "chapter"}
        else:
            test_data_clean = test_data
        
        success = test_highlight(API_URL, API_KEY, test_data_clean)
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

