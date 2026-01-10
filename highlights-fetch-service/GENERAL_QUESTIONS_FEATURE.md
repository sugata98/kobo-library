# General Questions Feature

## Overview

The Kobo AI Companion now supports **general question-answering** functionality, allowing you to ask the bot questions in two ways:

1. **Via Telegram** - Tag/mention the bot in any message
2. **Via API** - Send questions programmatically using the `/ask` endpoint

This extends the bot's capabilities beyond just analyzing highlights to being a general-purpose AI assistant.

---

## Usage Methods

### 1. Telegram Bot Tagging

Simply mention the bot in any message in your configured Telegram chat:

```
@YourBotName What are the key principles of distributed systems?
```

The bot will:

- Detect the mention
- Extract your question
- Generate a thoughtful response
- Reply to your message

**Example:**

```
User: @KoboBot What's the difference between REST and GraphQL?

Bot: 🤖 REST and GraphQL are both API architectures, but they differ fundamentally...
```

### 2. API Endpoint

Send questions programmatically via the `/ask` endpoint:

**Endpoint:** `POST /kobo-companion/ask`

**Headers:**

```
X-API-Key: your-kobo-api-key
Content-Type: application/json
```

**Request Body:**

```json
{
  "question": "What are the key principles of distributed systems?",
  "send_to_telegram": true
}
```

**Response:**

```json
{
  "question": "What are the key principles of distributed systems?",
  "answer": "Distributed systems are built on several fundamental principles...",
  "sent_to_telegram": true
}
```

**Parameters:**

- `question` (required): The question to ask the AI
- `send_to_telegram` (optional, default: `true`): Whether to also post the Q&A to Telegram

---

## How It Works

### Telegram Flow

1. **Message Detection**: The bot monitors all messages in the configured chat
2. **Mention Check**: Looks for `@botname` mentions (text or entity)
3. **Question Extraction**: Removes the bot mention and extracts the question
4. **AI Processing**: Sends the question to Gemini AI (using `gemini-3-flash-preview`)
5. **Response**: Replies to the user's message with the answer

### API Flow

1. **Authentication**: Validates the API key
2. **Question Processing**: Sends the question to Gemini AI
3. **Immediate Response**: Returns the answer in JSON format
4. **Background Task**: Optionally sends the Q&A to Telegram (if `send_to_telegram: true`)

---

## Implementation Details

### New Functions

#### `handle_general_question()`

```python
async def handle_general_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle general questions directed to the bot via mentions/tags.

    This handles when the user tags/mentions the bot to ask a general question,
    without needing to reply to a specific message.
    """
```

**Features:**

- Detects bot mentions (both `@username` and entity mentions)
- Extracts the question by removing the mention
- Sends typing indicator for better UX
- Generates and replies with the answer

#### `generate_general_answer()`

```python
async def generate_general_answer(self, question: str) -> str:
    """
    Generate a response to a general question (not tied to a specific highlight).
    Uses the text model for fast, high-quality responses.
    """
```

**AI Prompt Strategy:**

- Handles both technical and general topics
- Provides clear, concise explanations (2-3 paragraphs)
- Includes practical context and examples
- Offers additional insights and connections

### Handler Registration

The Telegram application now registers two handlers:

```python
# Handler 1: General questions (bot mentions)
application.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Entity("mention"),
        companion.handle_general_question
    )
)

# Handler 2: Follow-up questions (replies to bot messages)
application.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.REPLY,
        companion.handle_conversation
    )
)
```

**Order matters!** The mention handler is checked first, so tagging the bot takes precedence over replies.

---

## Use Cases

### 1. Quick Knowledge Lookup

```
@KoboBot What is eventual consistency?
```

### 2. Technical Clarification

```
@KoboBot Explain the CAP theorem in simple terms
```

### 3. Concept Comparison

```
@KoboBot What's the difference between microservices and monoliths?
```

### 4. Practical Guidance

```
@KoboBot When should I use Redis vs PostgreSQL?
```

### 5. API Integration

```bash
curl -X POST https://your-api.com/kobo-companion/ask \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the benefits of event-driven architecture?",
    "send_to_telegram": true
  }'
```

---

## Differences from Existing Features

| Feature                  | Trigger                     | Context                                 | Use Case                                           |
| ------------------------ | --------------------------- | --------------------------------------- | -------------------------------------------------- |
| **Highlight Analysis**   | Kobo device sends highlight | Book, author, chapter, highlighted text | Analyze specific passages from your reading        |
| **Follow-up Questions**  | Reply to bot's message      | Previous message thread                 | Ask follow-up questions about a specific highlight |
| **General Questions** ⭐ | Tag bot or API call         | No specific context                     | Ask any question, anytime                          |

---

## Configuration

No additional configuration is needed! The feature uses the existing settings:

- `TELEGRAM_ENABLED=True` - Enable Telegram integration
- `TELEGRAM_BOT_TOKEN` - Your bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your chat/group ID
- `GEMINI_API_KEY` - Your Google AI API key
- `GEMINI_MODEL` - Text model (default: `gemini-3-flash-preview`)
- `KOBO_API_KEY` - API key for the `/ask` endpoint

---

## Testing

### Test Telegram Bot Tagging

1. Open your Telegram chat where the bot is configured
2. Send a message: `@YourBotName What is a load balancer?`
3. The bot should reply with a detailed explanation

### Test API Endpoint

```bash
# Test with curl
curl -X POST http://localhost:8000/kobo-companion/ask \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain Docker containers",
    "send_to_telegram": false
  }'
```

**Expected Response:**

```json
{
  "question": "Explain Docker containers",
  "answer": "Docker containers are lightweight, standalone...",
  "sent_to_telegram": false
}
```

---

## Error Handling

The feature includes robust error handling:

1. **Invalid API Key**: Returns `401 Unauthorized`
2. **Service Unavailable**: Returns `503` if Telegram/AI is not configured
3. **Empty Questions**: Ignored (no response)
4. **AI Errors**: Returns user-friendly error messages
5. **Telegram Send Failures**: Logged but doesn't affect API response

---

## Performance

- **Response Time**: ~2-5 seconds (Gemini AI processing)
- **Typing Indicator**: Shows while processing for better UX
- **Background Tasks**: Telegram posting happens asynchronously (doesn't block API response)
- **Model**: Uses `gemini-3-flash-preview` for fast, high-quality responses

---

## Future Enhancements

Potential improvements:

1. **Conversation History**: Remember previous questions in a session
2. **Context Injection**: Automatically include recent highlights as context
3. **Multi-turn Conversations**: Support back-and-forth dialogue
4. **Voice Questions**: Support Telegram voice messages
5. **Rate Limiting**: Prevent abuse of the API endpoint
6. **Analytics**: Track popular questions and topics

---

## Troubleshooting

### Bot doesn't respond to mentions

1. Check that `TELEGRAM_ENABLED=True`
2. Verify bot username matches your mention
3. Ensure you're in the correct chat (matches `TELEGRAM_CHAT_ID`)
4. Check logs for errors: `docker logs highlights-fetch-service`

### API returns 503

1. Verify `TELEGRAM_ENABLED=True` in your environment
2. Check that all required credentials are set
3. Restart the service: `docker-compose restart highlights-fetch-service`

### Responses are slow

1. This is normal - Gemini AI takes 2-5 seconds
2. The typing indicator shows the bot is working
3. Consider using `send_to_telegram: false` for faster API responses

---

## Summary

The general questions feature makes your Kobo AI Companion more versatile:

✅ **Telegram Tagging**: Ask questions anytime by mentioning the bot  
✅ **API Endpoint**: Programmatic access for integrations  
✅ **Smart AI**: Uses Gemini 3 Flash for fast, accurate responses  
✅ **Flexible**: Works alongside existing highlight analysis features  
✅ **User-Friendly**: Simple to use, no configuration changes needed

Now your reading companion is also a general knowledge assistant! 🚀
