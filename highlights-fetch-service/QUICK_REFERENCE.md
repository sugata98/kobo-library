# 📚 Kobo AI Companion - Quick Reference

## 🎯 What It Does

**On Kobo**: Select text → Get instant AI explanation in dialog (2-3s)  
**On Telegram**: Full analysis + diagrams arrive automatically (background)

---

## 🔧 Configuration

### **Required Environment Variables**

```bash
# Backend API
KOBO_API_KEY=your-secure-random-key

# Telegram
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_CHAT_ID=your-chat-id
TELEGRAM_WEBHOOK_URL=https://api.readr.space

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image  # Set to empty to disable images
```

### **Kobo Script** (`ask_gemini.sh`)

```bash
API_URL="https://api.readr.space/kobo-ask"
API_KEY="your-secure-random-key"  # Must match KOBO_API_KEY above!
```

---

## 📡 API Endpoint

### `POST /kobo-ask`

**Request:**
```json
{
  "mode": "explain",
  "text": "selected text",
  "context": {
    "book": "Book Title",
    "author": "Author",
    "chapter": "Chapter 1"
  }
}
```

**Response:** Plain text explanation (for Kobo dialog)  
**Background:** Full analysis sent to Telegram with images

---

## 🚀 Quick Start

1. **Get API Keys:**
   - Telegram: @BotFather
   - Gemini: https://makersuite.google.com/app/apikey
   - Kobo: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

2. **Set Environment Variables** (Render dashboard)

3. **Update Kobo Script:**
   - Set `API_KEY` in `ask_gemini.sh`
   - Copy to `/mnt/onboard/.adds/nm/scripts/`

4. **Deploy:**
   ```bash
   git push origin main
   ```

5. **Test:**
   - Select text on Kobo
   - Click "Ask KoAI (Explain)"
   - See explanation in dialog
   - Check Telegram for full analysis

---

## 🎨 Image Generation

**Enabled by default** using `gemini-2.5-flash-image`

- Gemini automatically decides when images help
- Shows up in Telegram (not Kobo dialog)
- Works best for: architectures, diagrams, data structures

**To disable:**
```bash
GEMINI_IMAGE_MODEL=
```

---

## 🧪 Testing

```bash
# Update API key in test file
python test_kobo_api.py
```

---

## 📖 Documentation

- **Full Setup**: `KOBO_ASK_ENDPOINT.md`
- **Image Generation**: `IMAGE_GENERATION_SETUP.md`
- **Main README**: `KOBO_AI_COMPANION_README.md`

---

## 🛠️ Troubleshooting

**"Could not reach AI service"**
- Check WiFi on Kobo
- Verify API key matches in both places
- Check backend is running: `https://api.readr.space/health`

**No Telegram updates**
- Check `TELEGRAM_ENABLED=true`
- Verify bot token and chat ID
- Check Render logs for errors

**No images**
- Normal! Gemini only generates when helpful
- Try with technical content (algorithms, architectures)
- Check logs for "Image generation" messages

---

## 💡 Tips

1. **Best for technical books** - Engineering, CS, math, science
2. **Fast feedback** - Kobo dialog shows immediately
3. **Rich analysis** - Telegram has full details + images
4. **Conversation mode** - Reply in Telegram for follow-ups
5. **Smart images** - Gemini decides automatically

---

## 🎉 Summary

**Architecture**: Hybrid model approach
- `gemini-3-flash-preview` for fast text analysis
- `gemini-2.5-flash-image` for smart diagram generation

**Flow**:
```
Kobo → API → Immediate response (2-3s)
          → Background: Telegram + images (5-10s)
```

**Result**: Best reading companion for technical books! 🚀📚

