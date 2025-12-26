# B2 Two-Bucket Setup Guide

## Architecture Overview

**Recommended Setup** (Better Security):

```
┌─────────────────────────────────────────────────┐
│ B2 Cloud Storage                                 │
│                                                  │
│  ┌──────────────────────┐  ┌─────────────────┐ │
│  │ KoboSync (Bucket 1)  │  │ kobo-covers     │ │
│  │ - Read-Only Access   │  │ (Bucket 2)      │ │
│  │                      │  │ - Read-Write    │ │
│  │ ├── kobo/            │  │                 │ │
│  │ │   ├── KoboReader   │  │ ├── by-isbn/    │ │
│  │ │   │   .sqlite      │  │ ├── by-imageurl/│ │
│  │ │   └── markups/     │  │ └── by-title/   │ │
│  └──────────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Why Two Buckets?

✅ **Security**
- `KoboSync` = Read-only (your original Kobo data is safe from accidental modification)
- `kobo-covers` = Read-write (caching can write without risk to your data)

✅ **Separation of Concerns**
- Clear separation between synced data and cached data
- Different permission models for different purposes

✅ **Easier Management**
- Can delete/recreate covers bucket without affecting your data
- Can set different lifecycle rules for each bucket

## Step-by-Step Setup

### Step 1: Create New Bucket for Covers

1. **Go to B2 Buckets** → https://secure.backblaze.com/b2_buckets.htm

2. Click **"Create a Bucket"**

3. Configure:
   ```
   Bucket Unique Name: kobo-covers
   
   Files in Bucket are: Private
   
   Default Encryption: Disable (or enable if you prefer)
   
   Object Lock: Disable
   ```

4. Click **"Create a Bucket"**

### Step 2: Create Application Key for Covers Bucket

1. Click **"App Keys"** in left sidebar

2. Click **"Add a New Application Key"**

3. Configure:
   ```
   Name of Key: kobo-covers-readwrite
   
   Allow access to Bucket(s): kobo-covers  ← Select ONLY the covers bucket
   
   Type of Access: Read and Write  ← Full read-write access
   
   File name prefix (optional): [leave empty]
   
   Duration (optional): [leave empty]
   ```

4. Click **"Create New Key"**

5. **SAVE THESE CREDENTIALS** (you won't see them again!):
   ```
   keyID: 005xxxxxxxxxxxxx  ← Copy this!
   applicationKey: K005xxxxxxxxxxxxxxxxxxxxx  ← Copy this!
   ```

### Step 3: Update Environment Variables

#### For Local Development (`.env` file):

```bash
# ========================================
# KoboSync bucket (read-only for database)
# ========================================
B2_APPLICATION_KEY_ID=your_existing_readonly_key_id
B2_APPLICATION_KEY=your_existing_readonly_key
B2_BUCKET_NAME=KoboSync

# ========================================
# Covers bucket (read-write for caching)
# NEW - Add these three variables
# ========================================
B2_COVERS_APPLICATION_KEY_ID=005xxxxxxxxxxxxx
B2_COVERS_APPLICATION_KEY=K005xxxxxxxxxxxxxxxxxxxxx
B2_COVERS_BUCKET_NAME=kobo-covers

# ========================================
# Other settings
# ========================================
LOCAL_DB_PATH=/tmp/KoboReader.sqlite
```

#### For Render.com (Production):

Add these **NEW** environment variables (keep existing ones):

| Variable | Value |
|----------|-------|
| `B2_COVERS_APPLICATION_KEY_ID` | Your new key ID |
| `B2_COVERS_APPLICATION_KEY` | Your new application key |
| `B2_COVERS_BUCKET_NAME` | `kobo-covers` |

**Keep these existing variables unchanged:**
- `B2_APPLICATION_KEY_ID` (for KoboSync)
- `B2_APPLICATION_KEY` (for KoboSync)
- `B2_BUCKET_NAME` (KoboSync)

### Step 4: Restart Backend Service

**Local Development:**
```bash
# Stop current server (Ctrl+C)
cd highlights-fetch-service
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Render.com:**
- Automatically restarts after environment variable update

### Step 5: Verify It's Working

#### Test Backend Logs

Make a request:
```bash
curl "http://localhost:8000/api/books/_/cover?title=Clean+Code&author=Robert+Martin&isbn=9780132350884" -o test-cover.jpg
```

**First Request - Should see:**
```
💾 Checking B2 covers cache: by-isbn/9780132350884.jpg
🔍 Calling bookcover-api: https://bookcover.longitood.com/...
✅ Found cover from bookcover-api (ISBN: 9780132350884)
💾 Storing to B2 covers cache: by-isbn/9780132350884.jpg
✅ Stored cover to B2 cache for: Clean Code
```

**Second Request - Should see:**
```
💾 Checking B2 covers cache: by-isbn/9780132350884.jpg
✅ Found cover in B2 cache for: Clean Code
```

No external API call! Served from cache instantly.

#### Check B2 Dashboard

1. Go to **B2 Buckets** → `kobo-covers`
2. Click **"Browse Files"**
3. You should see:
   ```
   by-isbn/
   ├── 9780132350884.jpg
   └── ...
   
   by-imageurl/
   └── ...
   
   by-title/
   └── ...
   ```

### Step 6: Test Frontend

1. Open browser to `http://localhost:3000`
2. Open DevTools → Network tab
3. Covers should load fast
4. Check backend logs for cache hits

## What Was Changed in the Code

### 1. `config.py`
Added optional environment variables for covers bucket:
- `B2_COVERS_APPLICATION_KEY_ID`
- `B2_COVERS_APPLICATION_KEY`
- `B2_COVERS_BUCKET_NAME`

### 2. `b2.py`
Created two B2Service instances:
- `b2_service` - For KoboSync bucket (database, markups)
- `b2_covers_service` - For kobo-covers bucket (cached covers)

### 3. `endpoints.py`
Updated cover endpoint to use `b2_covers_service` for caching

### 4. `cover_service.py`
Simplified cache paths (no prefix needed since we have dedicated bucket)

## Bucket Comparison

| Feature | KoboSync Bucket | kobo-covers Bucket |
|---------|-----------------|-------------------|
| **Purpose** | Synced Kobo data | Cached covers |
| **Access** | Read-only | Read-write |
| **Contents** | KoboReader.sqlite, markups | Cover images |
| **Safety** | Protected | Can be recreated |
| **Key** | Your existing read-only key | New read-write key |

## Fallback Behavior

If you **don't** set the covers bucket variables:
- System automatically uses the main `KoboSync` bucket
- Covers stored in `KoboSync/kobo-covers/` folder
- Works fine, but less secure (write access to main bucket)

If you **do** set the covers bucket variables:
- System uses separate `kobo-covers` bucket
- Better security separation
- Recommended approach ✅

## Security Benefits

✅ **Main bucket remains read-only**
- Your Kobo database and markups are safe
- No risk of accidental deletion or modification

✅ **Covers bucket is isolated**
- If something goes wrong with caching, your data is safe
- Can delete and recreate covers bucket anytime

✅ **Separate credentials**
- Different keys for different purposes
- Can revoke covers key without affecting database access

## Cost

Two buckets cost the same as one:

**Storage**: $0.005/GB/month
- KoboSync: ~20MB (database + markups) = $0.0001/month
- kobo-covers: ~20MB (200 covers) = $0.0001/month
- **Total: ~$0.01/month** (essentially free!)

**Bandwidth**: Free with Cloudflare CDN integration

## Troubleshooting

**Error: "Failed to connect to Covers Cache bucket"**
- Check the three `B2_COVERS_*` environment variables are set correctly
- Verify bucket name is exactly `kobo-covers`
- Make sure the key has access to the covers bucket

**Covers not being cached:**
- Check logs for `✅ Stored cover to B2 cache` message
- Verify no ERROR messages after store attempt
- Test with: `curl -v http://localhost:8000/api/books/_/cover?title=Test&isbn=123`

**Can't see files in covers bucket:**
- Go to B2 dashboard → kobo-covers → Browse Files
- Files appear after first cover is cached
- Folder structure created automatically

## Migration from Single Bucket

If you were using a single bucket before:

1. Create new `kobo-covers` bucket
2. Add the three new environment variables
3. Restart service
4. Old covers in `KoboSync/kobo-covers/` will stay there (safe to delete)
5. New covers will go to the new `kobo-covers` bucket
6. No data loss, seamless migration

## Summary

✅ **Created**: New `kobo-covers` bucket for caching
✅ **Security**: KoboSync remains read-only
✅ **Configuration**: Added 3 new environment variables
✅ **Code**: Updated to use separate B2 service instances
✅ **Testing**: Verified caching works correctly
✅ **Cost**: Still essentially free (~$0.01/month total)

Your Kobo data is now protected while cover caching has the permissions it needs! 🎉

