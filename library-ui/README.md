# Readr UI

This directory contains the Next.js Progressive Web App (PWA) for browsing and organizing your reading highlights and annotations.

## Features

- 📱 **Progressive Web App** - Install on any device (desktop, mobile, tablet)
- 🔄 **Offline Support** - Access cached books and highlights without internet
- ⚡ **Lightning Fast** - Optimized caching strategies for instant loading
- 🎨 **Modern UI** - shadcn/ui components with dark mode support
- 🔐 **Secure** - Optional authentication to protect your data

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

**Note:** PWA features (service worker, offline support) are disabled in development mode. To test PWA functionality:

```bash
npm run build
npm start
```

Then open http://localhost:3000 and look for the install icon in your browser's address bar.

## PWA Features

### Offline Support
- Cached content is available even without internet
- Smart caching strategies for images, API calls, and fonts
- Fallback offline page when navigating to uncached content

### Installation
- **Desktop**: Click the install icon in your browser's address bar
- **Mobile (iOS)**: Tap Share → Add to Home Screen
- **Mobile (Android)**: Tap menu → Install app

### Caching Strategy
- **Book covers**: Cached for 30 days (instant loading)
- **Fonts**: Cached for 1 year (no FOUT)
- **API data**: Smart cache with 5-minute freshness
- **B2 assets**: Network-first with fallback to cache

See [docs/PWA_IMPLEMENTATION.md](../docs/PWA_IMPLEMENTATION.md) for complete technical details.
