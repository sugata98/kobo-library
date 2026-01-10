# Image Understanding Feature

## Overview

Your Kobo AI Companion now supports **image understanding**! You can send images to the bot and ask questions about them. The bot uses Gemini's vision capabilities to analyze images and provide detailed explanations.

## ✨ Capabilities

The bot can analyze and explain:

- 📊 **Technical diagrams** - System architectures, flowcharts, network diagrams
- 💻 **Code screenshots** - Analyze code snippets and explain what they do
- 📈 **Charts and graphs** - Interpret data visualizations and trends
- 📄 **Documents** - Read and summarize text in images
- 🖼️ **General photos** - Describe and contextualize any image content
- 🎨 **Whiteboard sketches** - Explain concepts drawn on whiteboards or paper

## 🚀 How to Use

### Method 1: Via Telegram (Easiest)

1. **Send an image** to your configured Telegram chat/group
2. **Add a caption** mentioning your bot and a question
3. **Wait for the response** - the bot will analyze and reply!

**Example:**

```
[Send image of a system architecture diagram]
Caption: @yourbotname What does this architecture diagram show?
```

**With no specific question:**

```
[Send image]
Caption: @yourbotname
```

(The bot will provide a general analysis)

### Method 2: Via API

**Endpoint:** `POST /api/ask-with-image`

**Headers:**

- `X-API-Key: YOUR_API_KEY`

**Form Data:**

- `image`: Image file (multipart/form-data)
- `question`: Your question about the image (optional, defaults to "What can you tell me about this image?")
- `send_to_telegram`: Boolean, whether to also send results to Telegram (default: true)

**Example using curl:**

```bash
curl -X POST http://your-server.com/api/ask-with-image \
  -H "X-API-Key: your-api-key-here" \
  -F "image=@diagram.png" \
  -F "question=Explain this system architecture" \
  -F "send_to_telegram=true"
```

**Example using Python:**

```python
import requests

url = "http://your-server.com/api/ask-with-image"
headers = {"X-API-Key": "your-api-key-here"}

with open("diagram.png", "rb") as image_file:
    files = {"image": image_file}
    data = {
        "question": "What does this diagram show?",
        "send_to_telegram": "true"
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.json())
```

**Response Format:**

```json
{
  "question": "What does this diagram show?",
  "answer": "This diagram illustrates a microservices architecture...",
  "image_filename": "diagram.png",
  "image_size_bytes": 245678,
  "sent_to_telegram": true
}
```

## 📝 Technical Details

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

### Limits

- **Maximum file size:** 20MB per image
- **API rate limits:** Subject to your Gemini API quota

### How It Works

1. **Image Upload/Receipt**

   - User sends image via Telegram or API
   - Image is downloaded and validated

2. **Vision Analysis**

   - Image is encoded to base64
   - Sent to Gemini (gemini-3-flash-preview) with multimodal capabilities
   - AI analyzes visual content and answers questions

3. **Response**
   - Analysis is returned immediately via API
   - Or sent as a Telegram reply to the user's message
   - Formatted with proper context and insights

### Privacy & Security

- Images are **not stored** - processed in memory only
- API requires authentication via `X-API-Key` header
- Telegram bot only responds in configured chat (via `TELEGRAM_CHAT_ID`)

## 🧪 Testing

Run the test script to verify everything works:

```bash
cd highlights-fetch-service
python test_image_understanding.py
```

This will:

- ✅ Check your configuration
- ✅ Create the companion service
- ✅ Test image analysis with a sample image
- ✅ Show you example usage patterns

## 🎯 Example Use Cases

### 1. Understanding Technical Diagrams

```
[Upload AWS architecture diagram]
@bot Explain each component and how they interact
```

### 2. Code Review

```
[Upload screenshot of Python code]
@bot What does this function do and are there any issues?
```

### 3. Data Analysis

```
[Upload chart showing sales trends]
@bot What insights can you derive from this chart?
```

### 4. Learning from Whiteboards

```
[Upload photo of whiteboard with algorithm explanation]
@bot Explain this algorithm step by step
```

### 5. Document Processing

```
[Upload photo of a book page or notes]
@bot Summarize the key points in this text
```

## 🔧 Configuration

Make sure these environment variables are set in your `.env`:

```bash
# Enable Telegram integration
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Gemini AI (vision model)
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-3-flash-preview  # Supports vision + text

# API authentication
KOBO_API_KEY=your_api_key_here
```

**Note:** The `GEMINI_MODEL` (gemini-3-flash-preview) supports both text and vision, so no additional model configuration is needed for image understanding.

## 📚 API Documentation

After starting your server, visit:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Look for the `/api/ask-with-image` endpoint to test interactively.

## 🐛 Troubleshooting

### Bot doesn't respond to images

- ✅ Check that `TELEGRAM_ENABLED=true`
- ✅ Verify you're tagging the bot correctly (@botusername)
- ✅ Ensure the image is sent to the configured `TELEGRAM_CHAT_ID`
- ✅ Check logs for any errors

### API returns 401 Unauthorized

- ✅ Verify `X-API-Key` header matches your `KOBO_API_KEY`
- ✅ Check that `KOBO_API_KEY` is set in your environment

### API returns 503 Service Unavailable

- ✅ Ensure `TELEGRAM_ENABLED=true`
- ✅ Verify all required credentials are configured
- ✅ Check application logs for initialization errors

### Vision analysis fails

- ✅ Ensure image is valid and not corrupted
- ✅ Check image size (must be under 20MB)
- ✅ Verify `GEMINI_API_KEY` has quota remaining
- ✅ Check that `GEMINI_MODEL` supports vision (gemini-3-flash-preview does)

## 🎉 Summary

You now have a powerful AI companion that can:

- 📖 Analyze text from your Kobo highlights
- 💬 Have conversations and answer general questions
- 🖼️ **Understand and explain images** (NEW!)
- 🎨 Generate visual diagrams to explain concepts

Just tag your bot with any image and ask away!
