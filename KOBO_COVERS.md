# Kobo Book Cover Storage

## ✨ Automatic Cover Fetching (Recommended)

**The library now automatically fetches book covers from free online APIs!** No manual syncing required.

The system uses:
- **Open Library API** (primary) - Free, no API key needed
- **Google Books API** (fallback) - Free, no API key needed

Covers are fetched automatically based on book title and author from your Kobo database. Just sync your database and covers will appear!

## Where Kobo Stores Book Covers

Kobo e-readers store book cover images in the following locations:

### 1. **On the Device File System**

Covers are stored in the `.kobo-images/` directory on your Kobo device:

```
.kobo-images/
  ├── {ContentID}-{hash}.png
  ├── {ContentID}-{hash}.jpg
  └── ...
```

**Typical paths:**
- `/mnt/onboard/.kobo-images/{ContentID}-{hash}.png`
- `.kobo-images/{ContentID}-{hash}.png` (relative path)

### 2. **In the Database**

The `content` table in `KoboReader.sqlite` contains an `ImageUrl` field that points to the cover image location:

- **Format**: `file:///mnt/onboard/.kobo-images/{ContentID}-{hash}.png`
- **Content**: File path reference, not the actual image data
- **Note**: Some older Kobo databases may store covers as BLOBs directly in the database, but this is less common

### 3. **Cover Image Characteristics**

- **Recommended dimensions**: 800x1224 pixels (3:4 aspect ratio)
- **Formats**: PNG or JPG
- **Naming**: Usually `{ContentID}-{hash}.{ext}` where hash is a unique identifier

## How to Get Covers into Your Library

### Option 1: Sync .kobo-images Directory to B2

If you're using KoSync or similar tools to sync your Kobo database, also sync the `.kobo-images/` directory:

1. **On your Kobo device**, the covers are in `.kobo-images/`
2. **Upload to B2** at one of these paths:
   - `kobo/.kobo-images/{filename}` (preserves original structure)
   - `kobo/covers/{ContentID}.jpg` (simplified structure)

### Option 2: Extract from Database ImageUrl

The backend automatically tries to use the `ImageUrl` from the database to locate covers in B2:

1. The `ImageUrl` field contains the original file path
2. The backend extracts the filename and tries to find it in B2 storage
3. It checks multiple possible B2 paths based on the ImageUrl

### Option 3: Manual Upload

If covers aren't synced automatically:

1. Connect your Kobo device to your computer
2. Navigate to `.kobo-images/` directory
3. Upload covers to B2 at: `kobo/covers/{ContentID}.jpg` or `kobo/.kobo-images/{original-filename}`

## Current Implementation

The `/books/{book_id}/cover` endpoint tries covers in this order:

1. **🆕 Free Online APIs** (automatic, no setup needed):
   - Open Library API - searches by title and author
   - Google Books API - fallback if Open Library doesn't have it
   
2. **B2 Storage** (if you've manually uploaded covers):
   - Database ImageUrl path - extracts filename from `ImageUrl` field
   - Common B2 paths:
     - `kobo/covers/{book_id}.jpg`
     - `kobo/covers/{book_id}.png`
     - `kobo/.kobo-images/{book_id}.jpg`
     - And several other variations

3. **Fallback**: Shows a placeholder icon if no cover is found

### Benefits of Automatic Fetching

- ✅ **No manual work** - Covers appear automatically
- ✅ **No storage costs** - Covers are fetched on-demand
- ✅ **Always up-to-date** - Uses the latest cover images from online sources
- ✅ **Works immediately** - Just sync your database, covers will load

## Troubleshooting

**No covers showing?**
- Check if `.kobo-images/` directory is synced to B2
- Verify the `ImageUrl` field in the database contains valid paths
- Ensure covers are uploaded to B2 with correct naming (matching ContentID)

**Covers not matching books?**
- Verify the filename in B2 matches the `ContentID` from the database
- Check that the `ImageUrl` field is correctly populated in the database

## Example: Finding Your Covers

1. **Query the database** to see ImageUrl values:
   ```sql
   SELECT ContentID, Title, ImageUrl FROM content WHERE ContentType = '6';
   ```

2. **Extract the filename** from ImageUrl (e.g., `file:///mnt/onboard/.kobo-images/abc123-def456.png` → `abc123-def456.png`)

3. **Upload to B2** at: `kobo/.kobo-images/abc123-def456.png` or `kobo/covers/{ContentID}.jpg`

