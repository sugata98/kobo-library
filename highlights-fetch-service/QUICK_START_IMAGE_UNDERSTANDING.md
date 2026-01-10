# Quick Start: Image Understanding 🖼️

## ✅ What's New

Your Telegram bot can now **understand images**! Just send any image and ask questions about it.

## 🚀 How to Use (3 Ways)

### 1️⃣ Telegram - Photo with Caption

Send any image to your configured Telegram chat with a caption mentioning your bot:

```
[Upload a diagram/screenshot/photo]
Caption: @yourbotname What does this show?
```

The bot will analyze the image and respond!

### 2️⃣ API - Simple Upload

```bash
curl -X POST http://localhost:8000/api/ask-with-image \
  -H "X-API-Key: your-api-key" \
  -F "image=@diagram.png" \
  -F "question=Explain this architecture"
```

### 3️⃣ Python Script Test

```bash
# Quick test
python test_image_understanding.py

# Test with your own image
python test_image_api.py path/to/image.jpg "What's in this image?"
```

## 📚 What Can It Analyze?

- ✅ **Technical diagrams** (architecture, flowcharts, UML)
- ✅ **Code screenshots** (analyze and explain code)
- ✅ **Charts/graphs** (interpret data trends)
- ✅ **Documents** (read and summarize text)
- ✅ **Whiteboards** (understand sketches and notes)
- ✅ **General photos** (describe any image)

## 🎯 Example Questions

| Image Type           | Example Question                                  |
| -------------------- | ------------------------------------------------- |
| Architecture diagram | "Explain each component and how they communicate" |
| Code screenshot      | "What does this function do? Any bugs?"           |
| Chart/graph          | "What trends do you see in this data?"            |
| Whiteboard           | "Explain this algorithm step by step"             |
| Document page        | "Summarize the key points"                        |
| Error message        | "What's causing this error and how to fix it?"    |

## ⚙️ Configuration

No new configuration needed! Uses existing settings:

```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-3-flash-preview  # Already supports vision!
KOBO_API_KEY=your_api_key
```

## 🧪 Test It Now

1. **Start your service:**

   ```bash
   cd highlights-fetch-service
   python main.py
   ```

2. **Run the test:**

   ```bash
   python test_image_understanding.py
   ```

3. **Try via Telegram:**
   - Send any image to your bot's chat
   - Caption: `@yourbotname explain this`
   - Watch the magic! ✨

## 📖 Full Documentation

See [IMAGE_UNDERSTANDING_FEATURE.md](./IMAGE_UNDERSTANDING_FEATURE.md) for complete details.

## 🔧 Troubleshooting

**Bot doesn't respond?**

- Check you tagged the bot correctly: `@yourbotname`
- Verify image is sent to the configured `TELEGRAM_CHAT_ID`
- Check logs for errors

**API returns 401?**

- Verify `X-API-Key` header matches `KOBO_API_KEY`

**API returns 503?**

- Ensure `TELEGRAM_ENABLED=true`
- Check all credentials are configured

## 🎉 That's It!

Your AI companion now has vision! Send images and ask away! 📸🤖
