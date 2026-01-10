# Kobo Modal Text Display Issues & Fixes

## Issues Identified from Debug Log

Looking at line 407 in your debug log, the system is working correctly:

```
SUCCESS: Response received (114 chars)
Response: 'Decouple storage from the notification server...'
Dialog output sent to stdout
```

But you're seeing three problems in the modal:

1. ❌ **Error message**: "non existent method or invalid parameter count"
2. ❌ **Emojis don't render**: ✨ and 📱 show as boxes or garbled text
3. ❌ **Text doesn't wrap**: Long explanations get cut off

---

## Root Causes

### 1. **Emoji Issue**
Kobo's NickelMenu `cmd_output` dialog doesn't support Unicode emojis. When it encounters `✨` or `📱`, it either:
- Shows garbled characters
- Causes parsing errors
- Breaks the dialog display

### 2. **Text Wrapping Issue**
NickelMenu's dialog has a fixed width (~40-50 characters) and doesn't automatically wrap long lines. If a line is too long:
- It gets truncated (cut off)
- User only sees the first part
- Rest is hidden

### 3. **Format Issue**
The current output format might have hidden characters or formatting that NickelMenu doesn't understand, causing the "invalid parameter count" error.

---

## Solution

Update the script's output section (around lines 182-186) to use **plain ASCII text only** and **manual line wrapping**:

### Current Code (Problematic):
```bash
# Output to stdout - NickelMenu will show this in a dialog
echo "✨ AI Explanation"
echo ""
echo "$RESPONSE"
echo ""
echo "📱 Full analysis sent to Telegram"
```

### Fixed Code:
```bash
# Output to stdout - NickelMenu will show this in a dialog
# Use plain ASCII (no emojis) and wrap text manually
echo "--- AI Explanation ---"
echo ""
# Wrap the response text to ~40 chars per line
echo "$RESPONSE" | fold -s -w 40
echo ""
echo "Full analysis sent to"
echo "Telegram!"
```

**Key Changes:**
1. ✅ Removed emojis (`✨` → `---`, `📱` → plain text)
2. ✅ Added `fold -s -w 40` to wrap text at 40 characters
3. ✅ Split long lines manually ("Full analysis sent to Telegram" → two lines)

---

## Alternative: Even Simpler Output

If the above still causes issues, use the **absolute simplest** format:

```bash
# Just output the response, nothing else
echo "$RESPONSE"
```

**Pros:**
- ✅ No special formatting to cause errors
- ✅ Just shows the AI explanation
- ✅ Most reliable

**Cons:**
- ⚠️ No header/footer
- ⚠️ User might not know it sent to Telegram

---

## Complete Fixed Script Section

Here's the complete fixed section for lines 172-201 of `ask_gemini.sh`:

```bash
# --- 6. USER FEEDBACK (The Native Dialog) ---

if [ $CURL_EXIT -eq 0 ] && [ -n "$RESPONSE" ]; then
    # Success: Output to stdout (NickelMenu's cmd_output will display this)
    # Backend returns a SHORT summary (1-2 sentences, max 200 chars)
    # Full analysis is sent to Telegram automatically
    echo "SUCCESS: Response received (${#RESPONSE} chars)" >> "$LOG_FILE"
    echo "Response: '$RESPONSE'" >> "$LOG_FILE"
    
    # Output to stdout - Plain ASCII only, wrapped to 40 chars
    echo "=== AI Explanation ==="
    echo ""
    # Wrap text to 40 characters per line
    echo "$RESPONSE" | fold -s -w 40
    echo ""
    echo "---"
    echo "Full details sent to"
    echo "your Telegram chat."
    
    echo "Dialog output sent to stdout" >> "$LOG_FILE"
else
    # Error: Output error to stdout
    echo "ERROR: curl failed with exit code $CURL_EXIT or empty response" >> "$LOG_FILE"
    echo "Response (if any): $RESPONSE" >> "$LOG_FILE"
    
    # Output to stdout - Plain ASCII only
    echo "=== Connection Error ==="
    echo ""
    echo "Could not reach the AI"
    echo "service. Please check"
    echo "your WiFi connection."
    echo ""
    echo "Error code: $CURL_EXIT"
fi
```

---

## Testing the Fix

### Step 1: Update the Script

Edit `/mnt/onboard/.adds/nm/scripts/ask_gemini.sh` and replace lines 172-201 with the code above.

### Step 2: Test with Simple Output First

For quickest testing, try the **ultra-simple version** first:

```bash
if [ $CURL_EXIT -eq 0 ] && [ -n "$RESPONSE" ]; then
    echo "Response received (${#RESPONSE} chars)" >> "$LOG_FILE"
    echo "Response: '$RESPONSE'" >> "$LOG_FILE"
    
    # Just output the response, nothing else
    echo "$RESPONSE"
    
    echo "Dialog output sent to stdout" >> "$LOG_FILE"
else
    echo "ERROR: curl failed" >> "$LOG_FILE"
    echo "Connection error. Check WiFi."
fi
```

### Step 3: Test on Kobo

1. Eject and restart Kobo
2. Select text and tap "Ask KoAI (Explain)"
3. **Expected:** Plain text dialog with AI explanation
4. Check `/mnt/onboard/kobo-ask-debug.log` for any errors

---

## Why This Happens

**NickelMenu's `cmd_output` limitations:**

| Issue | Cause | Fix |
|-------|-------|-----|
| Emojis don't render | Kobo firmware doesn't support Unicode emojis | Use ASCII only (`---`, `***`) |
| Text gets cut off | No automatic wrapping, fixed width dialog | Use `fold -s -w 40` |
| "Invalid parameter" error | Special characters or formatting | Plain text only |

---

## Expected Results

### Success Dialog (Simple Version):
```
Decouple storage from the 
notification server to enable 
independent scaling and improve 
architectural flexibility.
```

### Success Dialog (Formatted Version):
```
=== AI Explanation ===

Decouple storage from the 
notification server to enable 
independent scaling and improve 
architectural flexibility.

---
Full details sent to
your Telegram chat.
```

---

## Troubleshooting

### If dialog still shows error:

1. **Try ultra-simple version** (just `echo "$RESPONSE"`)
2. **Check for hidden characters:**
   ```bash
   cat -A /mnt/onboard/.adds/nm/scripts/ask_gemini.sh | tail -30
   ```
   Look for `^M` (Windows line endings) or other weird chars

3. **Verify NickelMenu syntax:**
   ```bash
   cat /mnt/onboard/.adds/nm/config
   # Should show: cmd_output :8000:
   ```

4. **Test manually:**
   ```bash
   /bin/sh /mnt/onboard/.adds/nm/scripts/ask_gemini.sh "test text"
   # Should output plain text only
   ```

---

## Summary

✅ **Root Cause:** Emojis and long unwr apped text breaking NickelMenu's dialog

✅ **Solution:** 
1. Remove all emojis (use ASCII alternatives)
2. Wrap text to 40 characters using `fold -s -w 40`
3. Keep output simple and plain

✅ **Best Practice:** 
- Test with ultra-simple output first (`echo "$RESPONSE"` only)
- Add formatting only if simple version works

🎯 **Result:** Clean, readable plain text dialog on Kobo!
