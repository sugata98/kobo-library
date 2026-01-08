# 🎨 Image Generation Setup

Get AI-generated diagrams for your technical reading! The bot automatically creates helpful visualizations for complex concepts.

---

## ✨ What You Get

When you highlight technical text, the bot:

1. 📝 Sends text analysis (fast, using `gemini-3-flash-preview`)
2. 🎨 Generates a diagram **if helpful** (using `gemini-2.5-flash-image`)
3. 💬 Lets you ask follow-up questions

**Perfect for:**

- 📚 Engineering & technical books
- 💻 Programming & CS books
- 🧮 Math & science textbooks
- 🏗️ System design books

---

## ⚙️ Configuration

### **Enable Images (Default)**

```bash
# .env
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

### **Disable Images**

```bash
# .env
GEMINI_IMAGE_MODEL=
# Or just don't set it
```

**That's it!** No Google Cloud setup, no service accounts, no complex configuration.

---

## 🚀 How It Works

### **Hybrid Model Approach**

```
Text Analysis (always)
├─ Model: gemini-3-flash-preview
├─ Speed: Fast (1-3 seconds)
└─ Quality: Excellent for explanations

Image Generation (optional)
├─ Model: gemini-2.5-flash-image
├─ Speed: 3-8 seconds (when generated)
├─ Smart: Gemini decides if image would help
└─ Quality: Clean technical diagrams
```

### **Example Flow**

1. **You highlight**: "Microservices communicate via REST APIs and message queues"
2. **Bot sends text analysis**: Explains microservices, communication patterns, benefits
3. **Bot generates diagram**: Shows 3 microservices, REST endpoints, message queue
4. **You reply**: "Tell me more about message queues"
5. **Bot responds**: Detailed explanation with examples

---

## 💰 Costs

| Service              | Free Tier           | Typical Usage | Cost              |
| -------------------- | ------------------- | ------------- | ----------------- |
| **Text Analysis**    | 1,500 req/day       | ~10-20/day    | ✅ Free           |
| **Image Generation** | Unknown (new model) | ~5-10/month   | ~$0.20-0.40/month |

**Total**: Essentially free for normal reading! 🎉

---

## 🎯 What Gets Visualized

### ✅ **Generates Images For:**

- System architectures (microservices, load balancers, databases)
- Data structures (trees, graphs, linked lists)
- Algorithms (flowcharts, sorting steps)
- Technical concepts (CAP theorem, MVC pattern)
- Workflows & processes
- Mathematical concepts

### ❌ **Skips Images For:**

- Simple definitions
- Historical facts
- Quotes or poetry
- Abstract ideas without visual components

**Gemini decides automatically!** No configuration needed.

---

## 📋 Setup Steps

### **1. Already Have Kobo AI Companion?**

Just add one line to your `.env`:

```bash
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

Redeploy. Done! 🎉

### **2. New Setup?**

Follow the main [KOBO_AI_COMPANION_README.md](./KOBO_AI_COMPANION_README.md), then add:

```bash
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

---

## 🛠️ Troubleshooting

### **No images being generated**

**This is normal!** Gemini only generates images when they're genuinely helpful.

Try with more technical content:

```bash
curl -X POST https://your-app.onrender.com/kobo-highlight \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A binary search tree maintains the property that left children are smaller than the parent",
    "book": "Introduction to Algorithms",
    "author": "CLRS"
  }'
```

### **Want to disable images?**

```bash
# In .env or Render environment variables
GEMINI_IMAGE_MODEL=
```

### **Check if enabled**

Look for this in your logs:

```
✅ Image generation enabled: gemini-2.5-flash-image
```

Or:

```
⚪ Image generation disabled
```

---

## 💡 Tips

1. **Works best with technical books** - Engineering, CS, math, science
2. **Gemini is smart** - It won't generate unnecessary images
3. **No extra setup** - Uses your existing `GEMINI_API_KEY`
4. **Easy to toggle** - Just set/unset `GEMINI_IMAGE_MODEL`
5. **Cost-effective** - Minimal usage for typical reading

---

## 🎉 Summary

**Before (Complex):**

- ❌ Google Cloud Project setup
- ❌ Vertex AI API enablement
- ❌ Service account creation
- ❌ JSON key management
- ❌ Multiple environment variables
- ❌ Complex dependencies

**After (Simple):**

- ✅ One environment variable: `GEMINI_IMAGE_MODEL=gemini-2.5-flash-image`
- ✅ Uses existing Gemini API key
- ✅ No extra dependencies
- ✅ No Google Cloud setup
- ✅ Gemini decides everything automatically

**Result**: Beautiful diagrams with zero hassle! 🚀📚
