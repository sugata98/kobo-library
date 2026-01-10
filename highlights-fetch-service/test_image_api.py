"""
API Test Script for Image Understanding

This script tests the /api/ask-with-image endpoint.

Usage:
    python test_image_api.py path/to/image.jpg "Your question here"
    
Example:
    python test_image_api.py diagram.png "What does this architecture show?"
"""

import sys
import requests
import os
from pathlib import Path


def test_image_api(image_path: str, question: str = "What can you tell me about this image?"):
    """
    Test the image understanding API endpoint
    
    Args:
        image_path: Path to the image file
        question: Question to ask about the image
    """
    
    # Configuration (update these or use environment variables)
    API_URL = os.getenv("API_URL", "http://localhost:8000/api/ask-with-image")
    API_KEY = os.getenv("KOBO_API_KEY", "your-api-key-here")
    
    print("=" * 70)
    print("Image Understanding API Test")
    print("=" * 70)
    print()
    
    # Validate image path
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        return
    
    # Get file info
    file_size = os.path.getsize(image_path)
    file_ext = Path(image_path).suffix.lower()
    
    # Validate file type
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if file_ext not in valid_extensions:
        print(f"❌ Error: Invalid file type '{file_ext}'. Supported: {', '.join(valid_extensions)}")
        return
    
    # Check file size
    max_size_mb = 20
    if file_size > max_size_mb * 1024 * 1024:
        print(f"❌ Error: File too large ({file_size / 1024 / 1024:.2f}MB). Max: {max_size_mb}MB")
        return
    
    print(f"📁 Image: {image_path}")
    print(f"📏 Size: {file_size / 1024:.2f} KB")
    print(f"❓ Question: {question}")
    print()
    print(f"🌐 API URL: {API_URL}")
    print()
    print("Sending request...")
    print()
    
    try:
        # Prepare request
        headers = {"X-API-Key": API_KEY}
        
        with open(image_path, "rb") as image_file:
            files = {"image": (os.path.basename(image_path), image_file)}
            data = {
                "question": question,
                "send_to_telegram": "true"
            }
            
            # Send request
            response = requests.post(
                API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
        
        print(f"📡 Response Status: {response.status_code}")
        print()
        
        # Handle response
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Success!")
            print()
            print("=" * 70)
            print("AI Analysis:")
            print("=" * 70)
            print(result['answer'])
            print("=" * 70)
            print()
            print(f"📊 Details:")
            print(f"  - Image filename: {result.get('image_filename')}")
            print(f"  - Image size: {result.get('image_size_bytes')} bytes")
            print(f"  - Sent to Telegram: {result.get('sent_to_telegram')}")
            
        elif response.status_code == 401:
            print("❌ Authentication failed!")
            print("   Make sure KOBO_API_KEY environment variable is set correctly.")
            print(f"   Current API Key: {API_KEY[:10]}...")
            
        elif response.status_code == 503:
            print("❌ Service unavailable!")
            print("   The AI Companion service is not running or not configured.")
            print("   Check that TELEGRAM_ENABLED=true and all credentials are set.")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Details: {error_detail}")
            except:
                print(f"   Response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print(f"   Could not connect to {API_URL}")
        print("   Make sure the server is running.")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout!")
        print("   Request took too long (>60s).")
        print("   The image might be too complex or the API is slow.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python test_image_api.py <image_path> [question]")
        print()
        print("Examples:")
        print('  python test_image_api.py diagram.png')
        print('  python test_image_api.py chart.jpg "What trends do you see?"')
        print('  python test_image_api.py code.png "Explain this code"')
        print()
        print("Environment Variables:")
        print("  API_URL       - API endpoint (default: http://localhost:8000/api/ask-with-image)")
        print("  KOBO_API_KEY  - Your API key for authentication")
        sys.exit(1)
    
    image_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "What can you tell me about this image?"
    
    test_image_api(image_path, question)


if __name__ == "__main__":
    main()
