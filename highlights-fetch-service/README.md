# Highlights Fetch Service

This directory contains the FastAPI backend service for syncing with B2 Cloud and parsing KoboReader.sqlite.

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

