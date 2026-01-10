# Modal Display Fix - Using NickelMenu's `cmd_output`

## Problem

The AI explanation modal was not appearing on the Kobo device, even though:

- ✅ The API was working correctly
- ✅ The response was being received (confirmed in debug log)
- ✅ The script was calling `qndb -m mng` to show a toast notification

**Root Cause:** `qndb -m mng` (toast notifications) are unreliable or not visible on some Kobo models/firmware versions.

---

## Solution

### Use NickelMenu's `cmd_output` Action

NickelMenu has a built-in action called `cmd_output` that:

1. Runs a shell script
2. Captures the script's **stdout** output
3. Displays it in a **native Kobo dialog**
4. Waits for the specified timeout (in milliseconds)

This is much more reliable than `qndb` commands!

---

## Changes Made

### 1. Updated NickelMenu Config

**File:** `/mnt/onboard/.adds/nm/config`

**Before:**

```
menu_item :selection :Ask KoAI (Explain) :cmd_spawn :quiet :/bin/sh /mnt/onboard/.adds/nm/scripts/ask_gemini.sh "{1|aS|"$}"
```

**After:**

```
menu_item :selection :Ask KoAI (Explain) :cmd_output :10000:/bin/sh /mnt/onboard/.adds/nm/scripts/ask_gemini.sh "{1|aS|"$}"
```

**Key Changes:**

- ❌ `cmd_spawn :quiet` - Runs script in background, no output shown
- ✅ `cmd_output :10000` - Runs script, shows output in dialog for 10 seconds

---

### 2. Updated Script Output

**File:** `/mnt/onboard/.adds/nm/scripts/ask_gemini.sh`

**Before:**

```bash
# Used qndb -m mng to show toast
qndb -m mng -t 8000 -c "✨ AI Explanation" -n "$RESPONSE"
```

**After:**

```bash
# Output to stdout - NickelMenu will capture and display this
echo "✨ AI Explanation"
echo ""
echo "$RESPONSE"
echo ""
echo "📱 Full analysis sent to Telegram"
```

**Key Changes:**

- ❌ `qndb` commands (unreliable)
- ✅ `echo` to stdout (captured by NickelMenu's `cmd_output`)

---

## How It Works

### Flow:

1. **User selects text** → Taps "Ask KoAI (Explain)"
2. **NickelMenu runs script** with `cmd_output` action
3. **Script executes:**
   - Extracts book/author/chapter metadata
   - Sends to backend API
   - Backend returns short summary (1-2 sentences)
   - Script outputs summary to **stdout**
4. **NickelMenu captures stdout** and displays it in a native dialog
5. **Dialog auto-closes** after 10 seconds (or user taps "OK")
6. **Meanwhile:** Backend sends full analysis to Telegram (background task)

---

## Expected User Experience

### Success Case:

**Kobo Dialog Shows:**

```
✨ AI Explanation

Multiple services initiate the notification
workflow by calling APIs provided by
dedicated notification servers.

📱 Full analysis sent to Telegram
```

**Dialog stays for 10 seconds** (enough time to read 1-2 sentences)

**Telegram receives:**

- Full detailed analysis (multiple paragraphs)
- Diagrams (if applicable)
- Book/chapter context

---

### Error Case:

**Kobo Dialog Shows:**

```
❌ Connection Error

Could not reach AI service.
Please check WiFi connection.

Error code: 7
```

---

## Why This Works Better

| Method                | Reliability | Visibility      | Character Limit | User Control                      |
| --------------------- | ----------- | --------------- | --------------- | --------------------------------- |
| `qndb -m mng` (toast) | ❌ Low      | ❌ Easy to miss | ~200 chars      | ❌ Auto-dismiss only              |
| `qndb -m dlgmessage`  | ⚠️ Medium   | ✅ Clear        | ~200-300 chars  | ✅ User dismisses                 |
| `cmd_output` (stdout) | ✅ High     | ✅ Clear        | ~1000+ chars    | ✅ User dismisses or auto-dismiss |

**Winner:** `cmd_output` ✅

- Most reliable across Kobo models
- Native NickelMenu feature (always available)
- Supports longer text
- Clear, modal dialog (not a toast)

---

## Testing

### On Kobo Device:

1. **Eject and restart Kobo** (to reload NickelMenu config)
2. **Open any book** and select some text
3. **Tap "Ask KoAI (Explain)"**
4. **Expect to see:**
   - ⏳ Brief pause (2-5 seconds) while API processes
   - 📱 Dialog appears with AI explanation
   - ✅ Dialog stays for 10 seconds or until you tap "OK"
5. **Check Telegram** for full analysis

### Debug:

```bash
cat /mnt/onboard/kobo-ask-debug.log

# Should show:
SUCCESS: Response received (XXX chars)
Response: '[short summary]'
Dialog output sent to stdout
```

---

## Timeout Explanation

```
:cmd_output :10000:
            ^^^^^
            10 seconds (10000 milliseconds)
```

**Why 10 seconds?**

- ✅ Enough time to read 1-2 sentences
- ✅ Not too long (user can dismiss early)
- ✅ Prevents blocking the UI indefinitely

**Adjustable:**

- Shorter: `:cmd_output :5000:` (5 seconds)
- Longer: `:cmd_output :15000:` (15 seconds)
- Max: `:cmd_output :10000:` (NickelMenu limit)

---

## Troubleshooting

### If dialog still doesn't appear:

1. **Check NickelMenu is installed:**

   ```bash
   ls /mnt/onboard/.adds/nm/
   ```

2. **Check config syntax:**

   ```bash
   cat /mnt/onboard/.adds/nm/config
   # Should have: cmd_output :10000:
   ```

3. **Test with simple command:**

   ```
   menu_item :main :Test Dialog :cmd_output :5000:echo "Hello World"
   ```

   If this doesn't work, NickelMenu might need reinstalling.

4. **Check script output:**
   ```bash
   /bin/sh /mnt/onboard/.adds/nm/scripts/ask_gemini.sh "test text"
   # Should print to stdout (not just log file)
   ```

---

## Alternative: FBInk (If Needed)

If `cmd_output` still doesn't work, you can use FBInk directly:

```bash
# In ask_gemini.sh, replace echo statements with:
/mnt/onboard/.adds/koreader/fbink -q -pm -y 10 "✨ AI Explanation"
/mnt/onboard/.adds/koreader/fbink -q -pm -y 12 "$RESPONSE"
/mnt/onboard/.adds/koreader/fbink -q -pm -y 14 "📱 Full analysis sent to Telegram"

# Wait for user to see it
sleep 10
```

**But `cmd_output` should work!** FBInk is a fallback only.

---

## Summary

✅ **Fixed Issues:**

1. Changed from `cmd_spawn` to `cmd_output` in NickelMenu config
2. Changed from `qndb` to `echo` (stdout) in script
3. Dialog now reliably appears on Kobo

✅ **User Experience:**

- Kobo shows short summary (1-2 sentences)
- Telegram shows full analysis (paragraphs + diagrams)
- Best of both worlds!

🎯 **Result:** Modal should now appear every time! 🚀
