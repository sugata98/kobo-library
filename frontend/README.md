# Frontend deployment configuration for Vercel

This directory contains the Next.js frontend application.

## Vercel Deployment

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Import your GitHub repository
3. Vercel will auto-detect Next.js from `vercel.json`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL (e.g., `https://your-backend.onrender.com/api`)

## Local Development

```bash
npm install
npm run dev
```

The app will be available at http://localhost:3000
