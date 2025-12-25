# Kobo Library

A monorepo for syncing and viewing Kobo e-reader highlights and markups from B2 Cloud.

## Structure

- `library-ui/`: Next.js application for viewing books and highlights.
- `highlights-fetch-service/`: FastAPI application for syncing with B2 and parsing `KoboReader.sqlite`.

## Prerequisites

- [Docker](https://www.docker.com/) (recommended for local development)
  - **Note:** On macOS, you must install **Docker Desktop** or **OrbStack** to run the Docker daemon. Installing `docker` via Homebrew only provides the CLI client.
- Node.js & Python 3.11+ (if running locally without Docker)
- A Backblaze B2 bucket containing your `KoboReader.sqlite` (synced via KoSync or similar).

## Setup

1. **Configure Backend Environment**:
   Create `highlights-fetch-service/.env` based on `highlights-fetch-service/example.env`:
   ```bash
   cp highlights-fetch-service/example.env highlights-fetch-service/.env
   # Edit highlights-fetch-service/.env with your B2 credentials
   ```

## Usage

### Option 1: Docker (Recommended)

1. Ensure Docker Desktop is running.
2. Run:
   ```bash
   docker-compose up --build
   ```
3. Access:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Option 2: Local Development (Manual)

If you cannot run Docker, run the services individually:

**Backend:**

```bash
cd highlights-fetch-service
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd library-ui
npm install
npm run dev
```

## Deployment

### Backend (Render)

1. **Create a new Web Service on Render:**

   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the Service:**

   - **Name**: `highlights-fetch-service` (or your preferred name)
   - **Root Directory**: `highlights-fetch-service`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables:**

   - `B2_APPLICATION_KEY_ID`: Your Backblaze B2 Application Key ID
   - `B2_APPLICATION_KEY`: Your Backblaze B2 Application Key
   - `B2_BUCKET_NAME`: Your B2 bucket name (e.g., `KoboSync`)
   - `LOCAL_DB_PATH`: `/tmp/KoboReader.sqlite` (default)

4. **Deploy:**
   - Render will automatically deploy on every push to your main branch
   - Note the service URL (e.g., `https://kobo-library-backend.onrender.com`)

### Frontend (Vercel)

1. **Install Vercel CLI** (optional, for CLI deployment):

   ```bash
   npm i -g vercel
   ```

2. **Deploy via Vercel Dashboard:**

   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - **Root Directory**: Leave as root (Vercel will detect `vercel.json`)
   - **Framework Preset**: Next.js (auto-detected)
   - **Build Command**: `cd library-ui && npm install && npm run build`
   - **Output Directory**: `library-ui/.next`

3. **Add Environment Variables:**

   - `NEXT_PUBLIC_API_URL`: Your Render backend URL (e.g., `https://kobo-library-backend.onrender.com/api`)

4. **Deploy:**
   - Vercel will automatically deploy on every push
   - Your site will be available at `https://your-project.vercel.app`

### Alternative: Deploy via CLI

**Backend (Render):**

```bash
# Install Render CLI
npm install -g render-cli

# Login
render login

# Deploy (if using render.yaml)
render deploy
```

**Frontend (Vercel):**

```bash
cd library-ui
vercel
# Follow the prompts
```

## Post-Deployment

1. **Update Frontend API URL:**

   - After deploying backend, update `NEXT_PUBLIC_API_URL` in Vercel environment variables
   - Redeploy frontend if needed

2. **Test the Deployment:**
   - Visit your Vercel URL
   - Click "Sync Data" to test B2 connection
   - Verify books and markups load correctly

## Troubleshooting

- **Backend not connecting to B2**: Verify environment variables are set correctly in Render
- **Frontend can't reach backend**: Check `NEXT_PUBLIC_API_URL` matches your Render service URL
- **CORS errors**: Backend already has CORS enabled for all origins (update in production if needed)
