# B2 Caching Setup (Optional)

## Current Status

✅ **B2 caching is implemented and working**  
⚠️ **B2 write permissions needed to enable caching**

The system currently works great with:

- ✅ Browser HTTP caching (30 days via Cache-Control headers)
- ✅ All cover sources (ImageUrl, bookcover-api, Open Library, Google Books)
- ✅ Fast response times

## Benefits of B2 Caching

Adding B2 write permissions enables:

1. **Global server-side cache** - Fetch once, serve to all users
2. **Persistent cache** - Survives browser clears and server restarts
3. **Cross-device** - Same user, different browsers benefit
4. **Reduced API calls** - Dramatically fewer external API calls
5. **Lower latency** - B2 serves faster than external APIs

## How to Enable B2 Caching

### Step 1: Create a new B2 Application Key with write permissions

1. Log into your Backblaze B2 account
2. Go to **App Keys** section
3. Click **Add a New Application Key**
4. Configure:
   - **Name**: `kobo-library-readwrite`
   - **Capabilities**: Select these permissions:
     - ✅ `readFiles`
     - ✅ `listFiles`
     - ✅ `readBuckets`
     - ✅ `listBuckets`
     - ✅ **`writeFiles`** ← This is the key permission needed
   - **File name prefix**: Leave empty or set to `kobo-covers/` (optional)
   - **Bucket**: Select your KoboSync bucket
5. Click **Create New Key**
6. **IMPORTANT**: Copy the `applicationKeyId` and `applicationKey` immediately (you won't see them again)

### Step 2: Update your environment variables

Replace your current B2 credentials with the new ones:

```bash
# .env or environment variables
B2_APPLICATION_KEY_ID=<new_key_id_with_write_permission>
B2_APPLICATION_KEY=<new_key_with_write_permission>
B2_BUCKET_NAME=KoboSync  # same bucket
```

### Step 3: Restart the backend service

```bash
cd highlights-fetch-service
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Verify B2 caching works

Make a request for a book cover:

```bash
curl "http://localhost:8000/api/books/_/cover?title=Clean+Code&author=Robert+Martin&isbn=9780132350884"
```

Check the logs - you should see:

```
💾 Checking B2 cache: kobo-covers/by-isbn/9780132350884.jpg
🔍 Calling bookcover-api: ...
✅ Found cover from bookcover-api
💾 Storing to B2 cache: kobo-covers/by-isbn/9780132350884.jpg
✅ Stored cover to B2 cache for: Clean Code
```

Make the same request again - you should see:

```
💾 Checking B2 cache: kobo-covers/by-isbn/9780132350884.jpg
✅ Found cover in B2 cache for: Clean Code
```

No external API call! The cover is served instantly from B2.

## B2 Storage Structure

Covers are organized in B2 as:

```
kobo-covers/
├── by-isbn/
│   ├── 9780132350884.jpg     (Clean Code)
│   ├── 9780547928227.jpg     (The Hobbit)
│   └── ...
├── by-imageurl/
│   ├── a1b2c3d4e5f6.jpg      (hash of ImageUrl)
│   └── ...
└── by-title/
    ├── f6e5d4c3b2a1.jpg      (hash of title+author)
    └── ...
```

## Cost Estimate

B2 Storage is extremely cheap:

- **Storage**: $0.005/GB/month
- **Bandwidth**: $0.01/GB (free with Cloudflare CDN)
- **API Calls**: Class B (download) - $0.004 per 10,000

**Example for 200 books:**

- 200 books × 100KB/cover = 20MB = **$0.0001/month** storage
- Bandwidth: Free with Cloudflare integration
- **Total cost: ~$0.01/month** 😄

## Current Behavior (Without Write Permissions)

The system works great even without B2 caching:

1. **ImageUrl covers** - Fetched directly from URLs in database
2. **Published books** - Fetched from bookcover-api/Open Library/Google Books
3. **Browser caching** - 30-day cache via Cache-Control headers
4. **Fast performance** - HTTP caching works well

The only difference is each user's first visit fetches from external APIs, vs fetching from B2 cache.

## Recommendation

**For single-user / personal use**: Browser caching is sufficient. B2 caching is optional.

**For multi-user / production**: Enable B2 caching for:

- Faster response times
- Reduced external API calls
- Better user experience
- Lower chance of rate limiting

## Troubleshooting

**Error: "unauthorized for application key"**

- Your B2 key doesn't have `writeFiles` permission
- Follow Step 1 above to create a new key with write access

**Error: "bucket not found"**

- Check `B2_BUCKET_NAME` environment variable
- Verify the bucket exists in your B2 account

**Covers not being cached:**

- Check logs for `💾 Storing to B2 cache` messages
- Verify no ERROR messages after the store attempt
- Confirm the kobo-covers/ folder exists in B2 (it's created automatically)
