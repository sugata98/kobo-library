# Deployment Guide: Vercel + Render

## Quick Start

### Step 1: Deploy Backend to Render

1. **Go to Render Dashboard:**

   - Visit https://dashboard.render.com/
   - Sign up/Login with GitHub

2. **Create New Web Service:**

   - Click "New +" → "Web Service"
   - Connect your GitHub repository (`sugata98/KoSync` or this repo)

3. **Configure Service:**

   ```
   Name: highlights-fetch-service
   Region: Choose closest to you
   Branch: main (or your default branch)
   Root Directory: highlights-fetch-service
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables:**
   Click "Environment" tab and add:

   ```
   B2_APPLICATION_KEY_ID = your_key_id
   B2_APPLICATION_KEY = your_key
   B2_BUCKET_NAME = KoboSync
   LOCAL_DB_PATH = /tmp/KoboReader.sqlite
   ```

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment (first deploy takes ~5 minutes)
   - **Copy the service URL** (e.g., `https://highlights-fetch-service.onrender.com`)

### Step 2: Deploy Frontend to Vercel

1. **Go to Vercel Dashboard:**

   - Visit https://vercel.com/dashboard
   - Sign up/Login with GitHub

2. **Import Project:**

   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Vercel will auto-detect Next.js

3. **Configure Project:**

   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `library-ui` ⚠️ **IMPORTANT: You MUST set this in the Vercel dashboard**
   - **Build Command**: Leave as default (or `npm install && npm run build`)
   - **Output Directory**: Leave as default (or `.next`)

   **Critical**: If you don't set Root Directory to `library-ui`, Vercel won't find Next.js and the build will fail.

4. **Add Environment Variable:**

   - Go to "Environment Variables"
   - Add:

   ```
   NEXT_PUBLIC_API_URL = https://highlights-fetch-service.onrender.com/api
   ```

   (This should match your Render backend service URL + `/api`)

5. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete
   - Your site will be live at `https://your-project.vercel.app`

### Step 3: Update CORS (Optional but Recommended)

After getting your Vercel URL, update Render backend:

- Go to Render → Your Service → Environment
- Add: `FRONTEND_URL = https://your-project.vercel.app`
- Redeploy backend

## Troubleshooting

**Backend Issues:**

- Check Render logs for errors
- Verify B2 credentials are correct
- Ensure database file exists in B2 at `kobo/KoboReader.sqlite`

**Frontend Issues:**

- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check browser console for CORS errors
- Ensure backend is running (check Render dashboard)

**Common Errors:**

- `502 Bad Gateway`: Backend might be sleeping (Render free tier spins down after inactivity)
- `CORS error`: Update `FRONTEND_URL` in Render environment variables
- `Database not found`: Run "Sync Data" button first

## Notes

- **Render Free Tier**: Services spin down after 15 minutes of inactivity. First request after spin-down takes ~30 seconds.
- **Vercel Free Tier**: Generous limits, should work fine for personal use.
- **B2 Storage**: Make sure your bucket is accessible with the provided credentials.
