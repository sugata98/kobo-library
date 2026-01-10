[![Better Stack Badge](https://uptime.betterstack.com/status-badges/v3/monitor/2c2v0.svg)](https://uptime.betterstack.com/?utm_source=status_badge)

# Readr

**Your personal space to revisit and connect reading highlights and annotations.**

Readr syncs, organizes, and helps you reflect on highlights and annotations from your Kobo e-reader. This is not an ebook reader—it's a tool for rediscovering and connecting insights from your reading journey.

## What is Readr?

Readr helps you:

- **Revisit** highlights and annotations from your Kobo reading sessions
- **Organize** insights by book, chapter, and timeline
- **Reflect** on your reading journey and connect ideas across books
- **Access offline** - fully-functional Progressive Web App (PWA) with offline support

## Features

- 📱 **Progressive Web App** - Install on any device (desktop, mobile, tablet)
- 🔄 **Offline Support** - Access your books and highlights without internet
- ⚡ **Lightning Fast** - Aggressive caching for instant page loads
- 🎨 **Modern UI** - Clean, minimal interface with dark mode
- 🔐 **Secure** - Optional authentication to protect your personal data
- 📚 **Rich Metadata** - View book details, chapters, and reading progress

## Structure

- `library-ui/`: Next.js application for browsing and organizing highlights and annotations
- `highlights-fetch-service/`: FastAPI service for syncing with B2 and parsing `KoboReader.sqlite`

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
   # Edit highlights-fetch-service/.env with your B2 credentials and authentication settings
   ```

2. **Set Up Authentication** (Recommended):
   Readr includes authentication to protect your personal reading data. See [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) for detailed instructions.

   Quick start:

   ```bash
   # Add to highlights-fetch-service/.env
   AUTH_ENABLED=true
   AUTH_USERNAME=your-username
   AUTH_PASSWORD=your-secure-password
   JWT_SECRET_KEY=your-generated-secret-key
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

   **Required:**

   - `B2_APPLICATION_KEY_ID`: Your Backblaze B2 Application Key ID
   - `B2_APPLICATION_KEY`: Your Backblaze B2 Application Key
   - `B2_BUCKET_NAME`: Your B2 bucket name (e.g., `KoboSync`)

   **Authentication (Recommended):**

   - `AUTH_ENABLED`: `true` (enable authentication)
   - `AUTH_USERNAME`: Your username for login
   - `AUTH_PASSWORD`: Your secure password
   - `JWT_SECRET_KEY`: Random secret key for JWT signing (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

   **Optional:**

   - `LOCAL_DB_PATH`: `/tmp/KoboReader.sqlite` (default)
   - `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: `43200` (30 days, default)

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

3. **Install as PWA:**
   - On desktop: Look for install icon in browser address bar
   - On mobile: Use "Add to Home Screen" from browser menu
   - Enjoy offline access to your highlights!

## Authentication

Readr includes built-in authentication to protect your personal reading data (highlights, annotations, markups) from public access.

**Features:**

- 🔒 Password-protected access
- 🍪 Secure httpOnly cookies (30-day sessions)
- 🎨 Clean login UI (shadcn blocks)
- ⚡ Zero-config frontend (automatic detection)

**Setup:** See [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) for detailed instructions.

**Quick Start:**

1. Add authentication env vars to backend (see above)
2. Deploy backend
3. Deploy frontend (no changes needed)
4. Navigate to your app → redirected to login
5. Enter credentials → you're in!

**To disable authentication** (development only):

```bash
AUTH_ENABLED=false
```

## Getting Latest Highlights

### How Data Syncing Works

1. **Backend syncs on startup**: When the backend starts, it downloads the latest `KoboReader.sqlite` from B2
2. **PWA caches data**: The frontend caches API responses for 5 minutes for fast loading
3. **Offline access**: Previously viewed content is available offline

### To See New Highlights

**Option 1: Restart Backend** (for new highlights from Kobo)

```bash
# Docker
docker-compose restart

# Or restart your backend service on Render
```

**Option 2: Browser Refresh** (after backend has latest data)

- Simply reload the page in your browser (⌘+R / Ctrl+R)
- Clears the API cache and fetches latest data

**Future Enhancement**: A "Sync & Refresh" button could be added to the UI to trigger backend sync without restart.

## Documentation

- **[PWA_IMPLEMENTATION.md](./docs/PWA_IMPLEMENTATION.md)** - Progressive Web App setup and features
- **[AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md)** - Complete authentication setup guide
- **[AUTHENTICATION_IMPLEMENTATION.md](./AUTHENTICATION_IMPLEMENTATION.md)** - Technical implementation details
- **[BOOKCOVER_API_INTEGRATION.md](./BOOKCOVER_API_INTEGRATION.md)** - Book cover fetching system
- **[B2_CACHING_IMPLEMENTATION_SUMMARY.md](./B2_CACHING_IMPLEMENTATION_SUMMARY.md)** - Cover caching with B2
- **[TABS_FEATURE_IMPLEMENTATION.md](./TABS_FEATURE_IMPLEMENTATION.md)** - Books vs Articles tabs

## Troubleshooting

- **Backend not connecting to B2**: Verify environment variables are set correctly in Render
- **Frontend can't reach backend**: Check `NEXT_PUBLIC_API_URL` matches your Render service URL
- **CORS errors**: Backend already has CORS enabled for all origins (update in production if needed)
- **Login not working**: Verify `AUTH_USERNAME`, `AUTH_PASSWORD`, and `JWT_SECRET_KEY` are set correctly
- **Session expires too quickly**: Increase `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30 days)
- **New highlights not showing**: Restart backend to re-sync from B2, then refresh browser
- **Offline content outdated**: Clear browser cache or reinstall PWA to fetch fresh data
