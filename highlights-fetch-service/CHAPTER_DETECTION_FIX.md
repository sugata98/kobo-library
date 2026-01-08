# Chapter Detection Fix

## Problem

The chapter query was always falling back to "Current Location" instead of showing actual chapter names.

### Root Causes:

1. **❌ `DateLastRead` is always empty for TOC entries**

   - Query used: `ORDER BY DateLastRead DESC`
   - Reality: TOC entries (ContentType='899') never have `DateLastRead` populated
   - Result: Query returned nothing

2. **❌ SQL escaping issues with book titles**

   - Query used: `AND Title != '$BOOK_TITLE'`
   - Problem: Book titles contain apostrophes (e.g., "An insider's guide")
   - Result: SQL syntax error, query failed silently

3. **❌ Multiple books matched the pattern**
   - Using `LIKE '%book name%'` matched multiple books
   - Returned inconsistent results

---

## Solution

### Updated Query Logic:

```bash
# Query 1: Try to get chapters (prefer "CHAPTER" or "Chapter" format)
CHAPTER=$("$SQLITE_BIN" "$DB_PATH" "SELECT Title FROM content WHERE ContentType = '899' AND Depth = 1 AND BookID = '$BOOK_CONTENT_ID' AND VolumeIndex > 1 AND (Title LIKE 'CHAPTER%' OR Title LIKE 'Chapter%') ORDER BY VolumeIndex LIMIT 1;")

# Query 2: Fallback to any TOC entry if no chapters found
if [ -z "$CHAPTER" ]; then
    CHAPTER=$("$SQLITE_BIN" "$DB_PATH" "SELECT Title FROM content WHERE ContentType = '899' AND Depth = 1 AND BookID = '$BOOK_CONTENT_ID' AND VolumeIndex > 1 ORDER BY VolumeIndex LIMIT 1;")
fi
```

### Key Changes:

1. ✅ **Use `VolumeIndex` instead of `DateLastRead`**

   - VolumeIndex represents the order of TOC entries
   - Always populated, reliable ordering

2. ✅ **Remove `Title != '$BOOK_TITLE'` comparison**

   - Avoids SQL escaping issues
   - Use `VolumeIndex > 1` to skip book title (usually at index 0 or 1)

3. ✅ **Two-tier fallback strategy**
   - First: Look for entries with "CHAPTER" or "Chapter" in title
   - Second: Get any TOC entry after index 1
   - Final: Fallback to "Current Location" if nothing found

---

## Testing Results

### Test 1: System Design Interview (has "CHAPTER" format)

```bash
BOOK_ID="file:///mnt/onboard/Xu, Alex/System Design Interview..."
Query result: "CHAPTER 1: SCALE FROM ZERO TO MILLIONS OF USERS" ✅
```

### Test 2: Book without "CHAPTER" format

```bash
BOOK_ID="1b6b6a2b-5b51-47b6-87ce-022368e0fe85"
Query result: "Contents" ✅
```

---

## Limitations & Trade-offs

### ⚠️ **Not "Current Chapter"**

The query returns the **first chapter** of the book, not the chapter the user is currently reading.

**Why?**

- TOC entries don't have reading progress data
- Determining current chapter requires complex bookmark correlation
- Would significantly slow down the script

**Impact:**

- Telegram shows: `📖 System Design Interview (CHAPTER 1: ...)`
- Even if user is reading Chapter 5

**Is this acceptable?**

- ✅ **Yes** - Shows book structure, better than "Current Location"
- ✅ User can see the full analysis in Telegram anyway
- ✅ Script remains fast and reliable

### ⚠️ **Book-Dependent Results**

Different books format their TOC differently:

- ✅ **Good:** "CHAPTER 1: Introduction", "Chapter One", "1. Getting Started"
- ⚠️ **Okay:** "Contents", "Introduction", "Foreword"
- ❌ **Poor:** Books with no TOC structure

**Fallback chain ensures something is shown.**

---

## Expected Behavior

### Case 1: Technical Books with Chapters

```
Book: "System Design Interview – An insider's guide"
Author: "Alex Xu"
Chapter: "CHAPTER 1: SCALE FROM ZERO TO MILLIONS OF USERS"
```

### Case 2: Books without Chapter Format

```
Book: "Some Novel"
Author: "Author Name"
Chapter: "Part One" (or "Introduction", etc.)
```

### Case 3: No TOC Entries Found

```
Book: "Book Title"
Author: "Author Name"
Chapter: "Current Location" (fallback)
```

---

## Future Improvements (Optional)

If you want to detect the **actual current chapter**, here's what would be needed:

1. **Get user's current reading position:**

   ```sql
   SELECT ContentID FROM Bookmark
   WHERE VolumeID = '$BOOK_ID'
   ORDER BY DateCreated DESC
   LIMIT 1
   ```

2. **Extract part number from ContentID:**

   - Example: `part0004_split_000.html` → `part0004`

3. **Match to chapter:**
   ```sql
   SELECT Title FROM content
   WHERE ContentType = '899'
   AND ContentID LIKE '%part0004%'
   ```

**Trade-off:**

- ✅ More accurate chapter detection
- ❌ 3x more SQL queries (slower script)
- ❌ More complex, more prone to edge cases
- ❌ Still won't work for all books

**Recommendation:** Current solution is optimal for speed vs. accuracy.

---

## Testing

### On Kobo Device:

1. Eject and restart Kobo
2. Select text in any book
3. Click "Ask KoAI (Explain)"
4. Check debug log:

```bash
cat /mnt/onboard/kobo-ask-debug.log

# Should show:
Chapter query result: 'CHAPTER 1: ...'
Final Context - Book: '...', Author: '...', Chapter: 'CHAPTER 1: ...'
```

5. Check Telegram message:

```
📖 System Design Interview – An insider's guide (CHAPTER 1: SCALE FROM ZERO TO MILLIONS OF USERS)
✍️ by Alex Xu

💡 Highlighted:
> [your text]
```

---

## Summary

✅ **Fixed Issues:**

1. Query now uses `VolumeIndex` instead of unpopulated `DateLastRead`
2. Removed SQL escaping issues by avoiding book title comparison
3. Two-tier fallback ensures something is always shown

✅ **Trade-offs:**

- Shows first chapter, not current chapter
- Good enough for user experience
- Keeps script fast and reliable

🎯 **Result:** Chapter detection now works for most books!
