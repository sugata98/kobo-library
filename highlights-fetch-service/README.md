# Highlights Fetch Service

This directory contains the FastAPI backend service for syncing with B2 Cloud and parsing KoboReader.sqlite.

## Book Cover Service

The service fetches book covers from multiple free APIs with the following priority:

1. **bookcover-api** (Primary) - https://bookcover.longitood.com
   - Fetches high-quality covers from Goodreads
   - Supports both ISBN-13 lookup and title/author search
   - Best quality and most reliable source

2. **Open Library API** (Fallback)
   - Free, no API key required
   - Good coverage for many books

3. **Google Books API** (Fallback)
   - Free, no API key required
   - Wide coverage as final fallback

The cover endpoint (`/books/{book_id}/cover`) accepts optional query parameters:
- `title` - Book title (required if not in database)
- `author` - Book author (optional, improves accuracy)
- `isbn` - ISBN-13 (optional, most accurate for bookcover-api)

Example:
```
GET /api/books/{book_id}/cover?title=Clean+Code&author=Robert+Martin&isbn=9780132350884
```

## Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set Root Directory to: `highlights-fetch-service`
4. Use the following settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `B2_APPLICATION_KEY_ID`
   - `B2_APPLICATION_KEY`
   - `B2_BUCKET_NAME`
   - `LOCAL_DB_PATH` (optional, defaults to `/tmp/KoboReader.sqlite`)

## Local Development

```bash
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

