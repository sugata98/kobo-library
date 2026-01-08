# 📱 Kobo Ask Endpoint - Complete Flow

## ✨ What It Does

The `/kobo-ask` endpoint provides **dual-mode** responses:

1. **Immediate**: Returns explanation to Kobo device (for dialog box)
2. **Background**: Sends full analysis to Telegram (with images)

**Best of both worlds!** 🎉

---

## 🔄 Complete Flow

```
┌─────────────────────────────────────────────────┐
│  User selects text on Kobo                     │
│  "Microservices communicate via REST APIs..."  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  NickelMenu triggers ask_gemini.sh              │
│  - Extracts book/author/chapter from DB        │
│  - Builds JSON payload                          │
│  - POSTs to /kobo-ask                          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Backend: POST /kobo-ask                        │
│  1. Validates API key                           │
│  2. Generates quick explanation (2-3s)          │
│  3. Returns plain text to Kobo                  │
│  4. Schedules background Telegram update        │
└──────────────┬─────────────────┬────────────────┘
               │                 │
               ▼                 ▼
    ┌──────────────┐   ┌───────────────────────┐
    │ Kobo Dialog  │   │ Background Task       │
    │ Shows text   │   │ - Send to Telegram    │
    │ immediately  │   │ - AI analysis         │
    │ (2-3 seconds)│   │ - Generate image      │
    └──────────────┘   └──────────┬────────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │ Telegram Messages   │
                        │ 1. Highlight        │
                        │ 2. AI Analysis      │
                        │ 3. Diagram (if any) │
                        └─────────────────────┘
```

---

## 📋 API Specification

### **Endpoint**

```
POST https://api.readr.space/kobo-ask
```

### **Headers**

```http
X-API-Key: your-kobo-api-key
Content-Type: application/json
```

### **Request Body**

```json
{
  "mode": "explain",
  "text": "The selected text to explain",
  "context": {
    "book": "Book Title",
    "author": "Author Name",
    "chapter": "Chapter 1",
    "device_id": "kobo-sarthak"
  }
}
```

### **Response**

```http
HTTP 200 OK
Content-Type: text/plain

[Plain text explanation from Gemini]
```

**Why plain text?**

- ✅ Kobo dialog displays it directly
- ✅ No JSON parsing needed
- ✅ Simple and fast
- ✅ Works perfectly with `qndb -m dlgmessage`

---

## 🎯 Key Features

### **1. Immediate Response**

- User gets explanation in **2-3 seconds**
- Shows in native Kobo dialog
- Can read comfortably
- No waiting for Telegram

### **2. Rich Telegram Integration**

- Full analysis sent in background
- Includes images/diagrams (if helpful)
- Threaded conversation
- Can ask follow-up questions

### **3. Smart Context**

- Extracts book/author/chapter from Kobo database
- Uses context for better explanations
- Tracks reading progress

---

## 💻 Client-Side (Kobo)

### **NickelMenu Config**

```bash
menu_item :selection :Ask KoAI (Explain) :cmd_spawn :quiet :/bin/sh /mnt/onboard/.adds/nm/scripts/ask_gemini.sh "explain" "{1|aS|"$}"
```

### **Shell Script** (`ask_gemini.sh`)

**Key sections:**

1. **Context Retrieval** (lines 31-68)

   ```sql
   -- Smart SQL query to get book, author, chapter
   -- Uses COALESCE for fallbacks
   ```

2. **JSON Construction** (lines 69-91)

   ```bash
   # Escapes quotes and backslashes properly
   # Builds valid JSON payload
   ```

3. **API Call** (lines 93-109)

   ```bash
   curl -k -s -f -m 20 -X POST "$API_URL" \
       -H "X-API-Key: $API_KEY" \
       -H "Content-Type: application/json" \
       -d "$JSON_DATA"
   ```

4. **Dialog Display** (lines 112-120)
   ```bash
   qndb -m dlgmessage -t "✨ AI Explanation" -m "$RESPONSE"
   ```

---

## 🔐 Security

### **API Key**

- Shared secret between Kobo and backend
- Set in both places:
  - **Kobo**: `ask_gemini.sh` line 5
  - **Backend**: `.env` `KOBO_API_KEY`

### **Generate Key**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Update both files with the same key!**

---

## 🚀 Setup

### **1. Backend Configuration**

```bash
# .env
KOBO_API_KEY=your-secure-random-key
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

### **2. Kobo Configuration**

```bash
# In ask_gemini.sh line 5
API_KEY="your-secure-random-key"  # Same as backend!
```

### **3. Deploy**

```bash
git push origin main
# Render will auto-deploy
```

---

## 🎓 Example Usage

### **User Action**

1. Opens book on Kobo
2. Long-presses to select text: "Binary search trees maintain ordering..."
3. Menu appears → Clicks "Ask KoAI (Explain)"

### **What Happens**

1. **Kobo dialog (2-3s)**: Shows explanation about BSTs, O(log n), use cases
2. **Telegram (5-10s)**:
   - Message with highlighted text
   - AI analysis
   - Diagram of BST structure

### **Follow-up**

- User replies in Telegram: "Tell me about AVL trees"
- Bot responds with comparison and more details

---

## 📊 Performance

| Operation              | Time            | Location                |
| ---------------------- | --------------- | ----------------------- |
| SQL query              | <100ms          | Kobo                    |
| JSON build             | <50ms           | Kobo                    |
| Network (WiFi)         | 500ms-2s        | Kobo → Cloud            |
| AI analysis            | 1-3s            | Backend                 |
| **Kobo sees response** | **2-5s total**  | ✅ Fast!                |
| Telegram send          | +1s             | Background              |
| Image generation       | +3-8s           | Background (if helpful) |
| **Telegram complete**  | **6-16s total** | ✅ Rich!                |

**User perception:**

- ✅ Instant feedback (Kobo dialog)
- ✅ Rich analysis arrives shortly (Telegram)
- ✅ Can continue reading while Telegram updates

---

## 🛠️ Troubleshooting

### **"Could not reach AI service"**

**Check:**

1. WiFi enabled on Kobo?
2. API key correct in `ask_gemini.sh`?
3. Backend deployed and running?
4. `TELEGRAM_ENABLED=true` in backend?

**Debug:**

```bash
# Test endpoint directly
curl -X POST https://api.readr.space/kobo-ask \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "explain",
    "text": "Test text",
    "context": {
      "book": "Test Book",
      "author": "Test Author"
    }
  }'
```

### **Empty dialog / no response**

**Check Kobo logs:**

```bash
# On Kobo via telnet/SSH
cat /mnt/onboard/.adds/nm/kobo-scripts.log
```

**Check backend logs:**

- Go to Render dashboard → Logs
- Look for: "Received explain request"

### **Telegram not updating**

**This is OK!** Telegram update is background task.

**But if it never arrives:**

1. Check `TELEGRAM_ENABLED=true`
2. Check bot token and chat ID
3. Check backend logs for errors

---

## 💡 Tips

### **1. Optimize for Technical Books**

The prompts are optimized for engineering/technical content. Works best with:

- Programming books
- System design books
- Math/science textbooks

### **2. Use for Quick Lookups**

Perfect for:

- "What does this term mean?"
- "Explain this concept"
- "Why does this work?"

### **3. Follow Up in Telegram**

- Initial explanation in Kobo dialog
- Deep dive in Telegram conversation
- Can ask multiple follow-ups

### **4. Images Arrive Automatically**

- Gemini decides when images help
- Shows up in Telegram (not Kobo dialog)
- Works best for architectures, diagrams, workflows

---

## 🎉 Summary

### **What You Have:**

1. **On-Device Experience**

   - Native Kobo integration
   - Fast explanations (2-5s)
   - No app switching

2. **Rich Cloud Experience**

   - Full AI analysis
   - Automatic diagrams
   - Conversation mode

3. **Smart Architecture**
   - Dual-mode response
   - Background processing
   - Efficient resource use

**Result**: Best reading companion for technical books! 🚀📚🎯
