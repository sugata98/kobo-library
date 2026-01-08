# Kobo AI Companion - FastAPI + Telegram Webhooks

A FastAPI-based backend service that provides AI-powered reading companion functionality for Kobo e-readers using Telegram and Google Gemini.

## 🎯 Overview

**Architecture**: FastAPI + Telegram Webhooks + Google Gemini AI

**Key Features**:
1. **API Endpoint** (`POST /kobo-highlight`): Receives highlights from Kobo device
2. **Telegram Integration**: Sends highlights to your Telegram group with AI analysis
3. **Conversation Mode**: Reply to AI analyses with follow-up questions
4. **Webhook-based**: Designed for deployment on Render.com (no polling)

## 🏗️ Architecture

```
Kobo Device → POST /kobo-highlight → FastAPI Backend
                                           ↓
                                  ┌────────┴────────┐
                                  ↓                 ↓
                          Telegram Message    Google Gemini AI
                          (with highlight)      (analysis)
                                  ↓                 ↓
                          Telegram Reply ←─────────┘
                          (AI analysis in thread)
                                  
User Reply in Telegram → Webhook → FastAPI Backend
                                        ↓
                                  Google Gemini AI
                                        ↓
                                  Telegram Reply
                                  (follow-up response)
```

## 📋 Prerequisites

- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Google Gemini API Key (from Google AI Studio)
- Render.com account (or similar hosting)

## 🚀 Quick Setup

### 1. Create Telegram Bot

```bash
# 1. Open Telegram, search for @BotFather
# 2. Send: /newbot
# 3. Follow prompts and copy the bot token
```

### 2. Get Chat ID

```bash
# 1. Create a group and add your bot
# 2. Send a message in the group
# 3. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# 4. Look for "chat":{"id":-1001234567890}
# 5. Copy that ID (negative for groups)
```

### 3. Get Gemini API Key

```bash
# 1. Visit: https://makersuite.google.com/app/apikey
# 2. Click "Create API Key"
# 3. Copy the key
```

### 4. Configure Environment

Create `.env`:

```bash
# Enable the service
TELEGRAM_ENABLED=true

# API Key for Kobo device (generate a secure random string)
KOBO_API_KEY=your-secure-random-key-here

# Telegram Configuration
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_WEBHOOK_URL=https://your-app-name.onrender.com

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-3-flash-preview
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run Locally (Development)

```bash
python main.py
# OR
uvicorn main:app --reload
```

## 🌐 Deployment on Render.com

### Step 1: Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository

### Step 2: Configure Service

**Build Command**:
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables** (add in Render dashboard):
```
TELEGRAM_ENABLED=true
KOBO_API_KEY=your-secure-key
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
TELEGRAM_WEBHOOK_URL=https://your-app-name.onrender.com
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-3-flash-preview
```

### Step 3: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment
3. Copy your Render URL: `https://your-app-name.onrender.com`
4. Update `TELEGRAM_WEBHOOK_URL` with this URL
5. Redeploy

### Step 4: Verify Webhook

Visit: `https://your-app-name.onrender.com/telegram-webhook-info`

You should see:
```json
{
  "url": "https://your-app-name.onrender.com/telegram-webhook",
  "pending_update_count": 0,
  ...
}
```

## 📡 API Endpoints

### `POST /kobo-highlight`

Send a highlight from your Kobo device.

**Headers**:
```
X-API-Key: your-secure-api-key
Content-Type: application/json
```

**Body**:
```json
{
  "text": "It is a truth universally acknowledged...",
  "book": "Pride and Prejudice",
  "author": "Jane Austen",
  "chapter": "Chapter 1"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Highlight sent to Telegram with AI analysis",
  "telegram_message_id": 12345
}
```

**cURL Example**:
```bash
curl -X POST https://your-app-name.onrender.com/kobo-highlight \
  -H "X-API-Key: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "War is peace. Freedom is slavery. Ignorance is strength.",
    "book": "1984",
    "author": "George Orwell",
    "chapter": "Part 1"
  }'
```

### `POST /telegram-webhook`

Webhook endpoint for Telegram updates (automatically configured).

### `GET /health`

Health check endpoint.

### `GET /telegram-webhook-info`

Get current webhook configuration (for debugging).

## 🔧 Kobo Device Configuration

You need to configure your Kobo to send highlights to the API. Here's a sample script:

### Option 1: Python Script (Recommended)

```python
import requests
import json

API_URL = "https://your-app-name.onrender.com/kobo-highlight"
API_KEY = "your-secure-api-key"

def send_highlight(text, book, author, chapter=None):
    """Send a Kobo highlight to the AI Companion API"""
    
    payload = {
        "text": text,
        "book": book,
        "author": author,
        "chapter": chapter
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        print(f"✅ Highlight sent: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Example usage
if __name__ == "__main__":
    send_highlight(
        text="The Answer to the Ultimate Question of Life, the Universe, and Everything is... 42.",
        book="The Hitchhiker's Guide to the Galaxy",
        author="Douglas Adams",
        chapter="Chapter 28"
    )
```

### Option 2: Shell Script

```bash
#!/bin/bash

API_URL="https://your-app-name.onrender.com/kobo-highlight"
API_KEY="your-secure-api-key"

# Extract from arguments
TEXT="$1"
BOOK="$2"
AUTHOR="$3"
CHAPTER="$4"

# Build JSON payload
if [ -n "$CHAPTER" ]; then
    PAYLOAD=$(cat <<EOF
{
  "text": "$TEXT",
  "book": "$BOOK",
  "author": "$AUTHOR",
  "chapter": "$CHAPTER"
}
EOF
)
else
    PAYLOAD=$(cat <<EOF
{
  "text": "$TEXT",
  "book": "$BOOK",
  "author": "$AUTHOR"
}
EOF
)
fi

# Send to API
curl -X POST "$API_URL" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
```

## 💬 Conversation Mode

After the bot sends an AI analysis, you can reply to it in Telegram with follow-up questions:

**Example**:
1. Bot sends: "📖 *1984* by George Orwell\n\n💡 Highlighted: War is peace..."
2. Bot replies with AI analysis
3. You reply to the analysis: "Tell me more about Orwell's use of paradox"
4. Bot replies with follow-up insights

**Features**:
- Maintains context from previous message
- Threaded conversations (using Telegram replies)
- Only responds to your replies (ignores other users)
- Ignores its own messages

## 🔒 Security

### API Key Authentication

All requests to `/kobo-highlight` must include a valid API key:

```bash
X-API-Key: your-secure-api-key
```

**Generate a secure key**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Environment Variables

Never commit `.env` to version control. Use Render's environment variables for production.

## 🛠️ Troubleshooting

### Bot doesn't send messages

**Check**:
1. Is `TELEGRAM_ENABLED=true`?
2. Is `TELEGRAM_BOT_TOKEN` correct?
3. Is `TELEGRAM_CHAT_ID` correct? (use `/getUpdates` to verify)
4. Did you add the bot to the group?

**Fix**:
```bash
# Test the API directly
curl -X POST https://your-app-name.onrender.com/kobo-highlight \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"text":"Test","book":"Test Book","author":"Test Author"}'
```

### Webhook not working

**Check webhook status**:
```bash
curl https://your-app-name.onrender.com/telegram-webhook-info
```

**Common issues**:
- `TELEGRAM_WEBHOOK_URL` doesn't match Render URL
- SSL certificate issues (Render provides HTTPS automatically)
- Webhook not set (check logs during startup)

**Fix**:
```bash
# Manually set webhook (if needed)
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d "url=https://your-app-name.onrender.com/telegram-webhook"
```

### Gemini API errors

**Common errors**:
- `API key not valid`: Check `GEMINI_API_KEY`
- `Quota exceeded`: Free tier = 15 req/min, 1500/day
- `Model not found`: Use `gemini-3-flash-preview`, `gemini-2.0-flash-exp`, `gemini-1.5-flash`, or `gemini-1.5-pro`

### Invalid API Key (401)

Your Kobo device is sending the wrong API key.

**Fix**:
1. Verify `KOBO_API_KEY` in `.env` matches what Kobo sends
2. Check for typos or extra spaces
3. Regenerate key if needed

## 📊 Monitoring

### Check Service Health

```bash
curl https://your-app-name.onrender.com/health
```

**Response**:
```json
{
  "status": "healthy",
  "companion": "initialized",
  "telegram": "initialized",
  "telegram_enabled": true
}
```

### Check Logs (Render)

1. Go to Render dashboard
2. Click on your service
3. Click "Logs" tab
4. Look for:
   - `✅ Kobo AI Companion initialized successfully`
   - `✅ Telegram webhook set to: ...`
   - `Received highlight from '...' by ...`

## 🎉 Example Usage

### 1. Send a highlight

```bash
curl -X POST https://your-app-name.onrender.com/kobo-highlight \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "In his blue gardens men and girls came and went like moths among the whisperings and the champagne and the stars.",
    "book": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "chapter": "Chapter 3"
  }'
```

### 2. Check Telegram

You should see:
1. **First message**: 📖 *The Great Gatsby* (Chapter 3)...
2. **Reply**: 🤖 **AI Analysis:** This passage captures the ephemeral quality of Gatsby's parties...

### 3. Reply with a question

Reply to the AI analysis in Telegram:
```
What does the moth simile symbolize?
```

Bot replies with follow-up insights!

## 📚 Files Overview

```
highlights-fetch-service/
├── main.py                          # Main FastAPI application (integrated with library + AI companion)
├── app/
│   ├── api/
│   │   └── kobo_companion.py        # AI companion API endpoints
│   ├── services/
│   │   └── kobo_ai_companion.py     # Telegram + AI service
│   └── core/
│       └── config.py                 # Configuration (updated)
├── requirements.txt                  # Dependencies
├── example.env                       # Environment template
└── KOBO_AI_COMPANION_README.md      # This file
```

## 🚀 Quick Test

After deployment, test the complete flow:

```bash
# 1. Health check
curl https://your-app-name.onrender.com/health

# 2. Send test highlight
curl -X POST https://your-app-name.onrender.com/kobo-highlight \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"text":"Test highlight","book":"Test","author":"Tester"}'

# 3. Check Telegram for messages

# 4. Reply to bot's message with: "Tell me more"

# 5. Bot should reply with follow-up!
```

## 🎓 How It Works

### Flow 1: Highlight Submission

```
1. Kobo sends POST /kobo-highlight
2. API validates X-API-Key header
3. API sends highlight to Telegram
4. API calls Gemini for analysis
5. API replies with analysis (creates thread)
6. Returns success + message_id
```

### Flow 2: Conversation

```
1. User replies to bot's message in Telegram
2. Telegram sends webhook to /telegram-webhook
3. Bot checks: is it a reply to my message?
4. Bot reads user question + previous context
5. Bot calls Gemini with both
6. Bot replies to user in same thread
```

## 💡 Tips

1. **Test locally first**: Use `uvicorn main:app --reload`
2. **Check webhook**: Visit `/telegram-webhook-info` after deployment
3. **Monitor logs**: Use Render logs to debug issues
4. **Rate limits**: Gemini free tier = 15 req/min (plenty for reading)
5. **Security**: Never expose `KOBO_API_KEY` or `TELEGRAM_BOT_TOKEN`

## 📖 Next Steps

1. Configure your Kobo device to call the API
2. Read a book and highlight passages
3. Get instant AI insights in Telegram
4. Ask follow-up questions
5. Enjoy AI-powered reading! 📚✨

---

**Status**: ✅ Production-ready for Render deployment

**Need help?** Check troubleshooting section or create an issue.

