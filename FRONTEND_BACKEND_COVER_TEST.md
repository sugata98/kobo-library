# Frontend → Backend → bookcover-api Integration Test

## What Changed

✅ **Frontend now calls backend endpoint instead of direct Google Books API**

### Old Flow (Direct Client-Side API Calls):
```
Browser → Google Books API (visible in Network tab)
Browser → Open Library API
```

### New Flow (Through Backend):
```
Browser → Backend API → bookcover-api (Goodreads)
                      → Open Library (fallback)
                      → Google Books (fallback)
```

## Testing in Browser

1. **Open your browser** to `http://localhost:3000`

2. **Open DevTools Network Tab** (F12 → Network)

3. **Refresh the page** to load book covers

4. **What you should see in Network tab:**
   - ✅ Requests to `localhost:8000/api/books/_/cover?title=...&author=...&isbn=...`
   - ❌ NO requests to `googleapis.com`
   - ❌ NO requests to `openlibrary.org` (from frontend)

5. **What you should see in backend logs** (terminal running uvicorn):
   ```
   🔍 Calling bookcover-api: https://bookcover.longitood.com/bookcover/...
   📡 bookcover-api response: status=200
   📥 Fetching image from: https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/books/...
   ✅ Found cover from bookcover-api (ISBN: ...)
   ```

## Example Backend Logs

When you load a book list, you should see:

```
INFO:app.api.endpoints:Fetching cover for book_id: _, title: Clean Code, author: Robert Martin, isbn: 9780132350884
INFO:app.services.cover_service:Fetching cover for: 'Clean Code' by Robert Martin (ISBN: 9780132350884)
INFO:app.services.cover_service:🔍 Calling bookcover-api: https://bookcover.longitood.com/bookcover/9780132350884
INFO:app.services.cover_service:📡 bookcover-api response: status=200
INFO:app.services.cover_service:📥 Fetching image from: https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/books/...
INFO:app.services.cover_service:✅ Found cover from bookcover-api (ISBN: 9780132350884)
INFO:app.api.endpoints:Found cover from online API for: Clean Code
```

## Verification Checklist

- [ ] No `googleapis.com` requests in browser Network tab
- [ ] Backend logs show `🔍 Calling bookcover-api`
- [ ] Backend logs show `✅ Found cover from bookcover-api`
- [ ] Book covers are loading correctly on the page
- [ ] Covers are cached (subsequent page visits don't fetch again)

## Architecture Benefits

1. **All API calls centralized in backend**
   - Easier to monitor and debug
   - Single point for rate limiting
   - Better error handling

2. **Frontend simplified**
   - Just calls backend endpoint
   - No need to handle multiple API sources
   - Cleaner client-side code

3. **Better caching**
   - Backend can implement server-side caching
   - Frontend caches blob URLs
   - Reduced external API calls

4. **Priority system works**
   - bookcover-api (Goodreads) tried first - best quality
   - Open Library as fallback
   - Google Books as final fallback

## Clear Browser Cache

If you want to force fresh fetches to test (bypass the 30-day HTTP cache):

### Option 1: Hard Refresh (Easiest)
- **Windows/Linux**: `Ctrl + Shift + R`
- **Mac**: `Cmd + Shift + R`

This forces the browser to bypass its HTTP cache and fetch fresh covers from the backend.

### Option 2: Disable Cache in DevTools
1. Open DevTools (`F12` or `Right-click → Inspect`)
2. Go to **Network** tab
3. Check **"Disable cache"** checkbox
4. Keep DevTools open while testing
5. Refresh the page

### Option 3: Clear Cached Images and Files
1. Open DevTools → **Application** tab
2. Expand **Storage** in sidebar
3. Click **"Clear site data"** button
4. Or selectively clear: **Cache Storage** → Right-click → Delete
5. Refresh the page

**Note**: localStorage is no longer used for cover caching. All caching is handled via standard HTTP Cache-Control headers (30-day expiration).

## Troubleshooting

**If you still see Google Books API calls:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Clear browser cache
- Check that Next.js dev server reloaded the changes

**If covers aren't loading:**
- Check backend logs for errors
- Verify backend is running on port 8000
- Check CORS settings if needed
- Verify `NEXT_PUBLIC_API_URL` environment variable

**If you see fallback to Open Library:**
- This is normal if bookcover-api doesn't have the book
- Check backend logs for the cascade:
  ```
  🔍 Calling bookcover-api: ...
  ❌ bookcover-api search failed: status=404
  Trying Open Library...
  ```

