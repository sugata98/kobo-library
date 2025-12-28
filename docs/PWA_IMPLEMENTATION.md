# PWA Implementation for Readr

## Overview

Readr is now a fully-functional Progressive Web App (PWA), enabling users to install it on their devices and access content offline with app-like behavior.

## What's Been Implemented

### 1. Service Worker

- **Generated via**: `@ducanh2912/next-pwa`
- **Location**: `public/sw.js` (auto-generated during build)
- **Behavior**:
  - Registers automatically on app load
  - Activates immediately via `skipWaiting: true`
  - Claims clients immediately via `clientsClaim: true`

### 2. Web App Manifest

- **Location**: `public/site.webmanifest`
- **Features**:
  - App name: "Readr - Your Reading Highlights"
  - Display mode: `standalone` (full-screen, app-like)
  - Orientation: `portrait-primary`
  - Multiple icon sizes (16x16, 32x32, 192x192, 512x512)
  - Theme colors for light/dark mode
  - App shortcuts for quick access
  - Categories: books, productivity, education

### 3. Caching Strategies

#### **Google Fonts** - CacheFirst

- Cache fonts for 1 year
- Max 4 entries
- Ensures fonts load instantly, even offline

#### **B2 API Assets** - NetworkFirst

- Network timeout: 10 seconds
- Falls back to cache if network fails
- Cache for 1 week
- Max 100 entries
- Ensures book covers and data load fast

#### **Images** - CacheFirst

- Cache for 30 days
- Max 200 entries
- Covers all image formats (PNG, JPG, SVG, WebP, etc.)

#### **API Routes** - NetworkFirst

- Network timeout: 10 seconds
- Cache for 5 minutes
- Max 50 entries
- Fresh data prioritized, cache as fallback

### 4. Offline Fallback Page

- **Route**: `/offline`
- **Purpose**: Shown when user navigates to uncached pages while offline
- **Features**:
  - Clear offline indicator
  - Link back to library (which may be cached)
  - User-friendly messaging about cached content

### 5. Enhanced Metadata

- Apple Web App capable
- Optimized for mobile installation
- Open Graph tags for social sharing
- Twitter Card support
- Viewport configuration for proper scaling
- Dynamic theme colors based on system preference

## Installation Behavior

### Desktop (Chrome, Edge, Brave)

- "Install" icon appears in address bar
- Click to install as standalone app
- App opens in its own window
- Appears in Start Menu/Applications folder

### Mobile (iOS Safari)

- Tap "Share" button
- Tap "Add to Home Screen"
- App icon appears on home screen
- Opens in fullscreen (no browser chrome)

### Android

- Automatic install banner may appear
- Or tap menu → "Install app"
- App appears in app drawer
- Full native-like experience

## Development vs Production

### Development Mode

- PWA is **disabled** in development (NODE_ENV === "development")
- No service worker registration
- No caching behaviors
- Hot reload works normally

### Production Mode

- PWA **enabled** automatically
- Service worker generates during `npm run build`
- All caching strategies active
- Offline support enabled

## Build Configuration

### Next.js Config (`next.config.ts`)

```typescript
withPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  sw: "sw.js",
  fallbacks: { document: "/offline" },
  workboxOptions: {
    disableDevLogs: true,
    skipWaiting: true,
    clientsClaim: true,
    runtimeCaching: [
      /* strategies */
    ],
  },
})(nextConfig);
```

### Build Command

```bash
npm run build --webpack
```

- Uses webpack instead of Turbopack (required for PWA plugin compatibility)
- Generates service worker and workbox files

## Files Generated During Build

**Automatically created in `public/`:**

- `sw.js` - Service worker
- `sw.js.map` - Source map for debugging
- `workbox-*.js` - Workbox runtime
- `workbox-*.js.map` - Workbox source map

**Git ignored via `.gitignore`:**

```
**/public/sw.js
**/public/sw.js.map
**/public/workbox-*.js
**/public/workbox-*.js.map
```

## Testing PWA Locally

### 1. Build for Production

```bash
cd library-ui
npm run build
npm start
```

### 2. Test with Chrome DevTools

1. Open app in Chrome
2. Open DevTools (F12)
3. Go to "Application" tab
4. Check:
   - **Manifest**: Verify manifest loads correctly
   - **Service Workers**: Verify SW is registered and running
   - **Cache Storage**: View cached resources
   - **Offline**: Toggle offline mode and test

### 3. Install Locally

- Look for install icon in address bar
- Click to install
- Test app in standalone window

## Lighthouse PWA Score

Run Lighthouse audit to verify PWA compliance:

```bash
# After starting production build
npx lighthouse http://localhost:3000 --view --preset=desktop
```

**Expected scores:**

- ✅ Installable
- ✅ PWA-optimized
- ✅ Service worker registered
- ✅ Offline capable
- ✅ Proper manifest
- ✅ HTTPS (in production)

## User Benefits

### For Readers

1. **Install on Any Device**: Desktop, mobile, tablet
2. **Offline Access**: View cached books and highlights without internet
3. **Fast Loading**: Aggressive caching means instant loads
4. **Native Feel**: No browser chrome, full-screen experience
5. **Save Data**: Fewer network requests after initial cache

### Performance Improvements

- **Book covers**: Cached for 30 days (instant load)
- **Fonts**: Cached for 1 year (no flash of unstyled text)
- **API data**: Smart cache for 5 minutes (balance freshness and speed)
- **Page navigation**: Instant, even when offline

## Data Freshness Strategy

### How NetworkFirst Works

The PWA uses **NetworkFirst** strategy for API calls:

```
User Opens App → Service Worker:
  1. Try network first (10s timeout)
  2. If online + successful → Return fresh data ✅
  3. If offline/timeout → Fall back to cache (max 5 minutes old)
```

### Automatic Fresh Data

**The app automatically shows latest data** when:

- ✅ User opens/reopens the installed PWA (if online)
- ✅ User navigates between pages (if online)
- ✅ Backend is reachable within 10s timeout
- ✅ Backend has synced latest data from B2

**No manual refresh needed** - NetworkFirst ensures fresh data by default.

### Data Flow

1. **Kobo device** → KoSync → **B2 bucket** (KoboReader.sqlite)
2. **Backend startup** → Downloads from B2
3. **PWA opens** → Fetches from backend (NetworkFirst)
4. **Cache fallback** → Only used if offline/timeout

### Getting New Highlights from Kobo

**Step 1:** Ensure backend has synced from B2

- Backend syncs on startup
- Restart backend to force re-sync

**Step 2:** Open the app

- PWA automatically fetches fresh data
- No manual action needed

### Why No Manual Refresh Button?

**Not needed because:**

- NetworkFirst already fetches fresh data on app open
- Cache only used as offline fallback
- Refresh button would be redundant and confusing
- Users expect app to "just work"

### Why No Background Sync API?

**Background Sync API** is designed for:

- Queuing offline writes (form submissions, uploads)
- Syncing user-generated data TO the server

**Readr doesn't need it because:**

- Read-only app (no user data to sync)
- Data flows one-way: B2 → Backend → Frontend
- NetworkFirst handles data freshness automatically

## Future Enhancements

### Possible Improvements

1. **Backend Sync Trigger**: Add UI button to trigger backend B2 sync (not needed with auto-sync)
2. **Push Notifications**: Notify users of new books/highlights (requires backend support)
3. **Periodic Background Sync**: Auto-update cache periodically (if sync endpoint exposed)
4. **Share Target**: Share quotes/highlights from other apps to Readr
5. **Install Analytics**: Track how many users install the PWA
6. **Pull-to-Refresh**: Mobile-friendly gesture to refresh data

### Advanced Caching

1. **Precache critical pages**: Cache library and recent books during install
2. **Predictive prefetching**: Preload book details when hovering over books
3. **Smart cache invalidation**: Clear old caches automatically

## Troubleshooting

### Service Worker Not Updating

```javascript
// In browser console
navigator.serviceWorker.getRegistrations().then(function (registrations) {
  registrations.forEach((r) => r.unregister());
});
location.reload();
```

### Clear All Caches

```javascript
// In browser console
caches.keys().then((keys) => {
  keys.forEach((key) => caches.delete(key));
});
```

### Force Update

- Increment version in `site.webmanifest`
- Rebuild and redeploy
- Service worker will detect changes and update

## Browser Support

| Browser          | Support    | Notes               |
| ---------------- | ---------- | ------------------- |
| Chrome 67+       | ✅ Full    | Desktop & mobile    |
| Edge 79+         | ✅ Full    | Desktop & mobile    |
| Safari 11.1+     | ⚠️ Partial | Limited SW features |
| Firefox 62+      | ✅ Full    | Desktop & mobile    |
| Samsung Internet | ✅ Full    | Full support        |

## Production Deployment

### Vercel (Recommended)

- PWA works automatically
- HTTPS enabled by default
- Service worker served correctly
- No additional configuration needed

### Manual Deployment

Ensure:

1. ✅ HTTPS enabled (required for Service Workers)
2. ✅ `sw.js` served with correct MIME type (`text/javascript`)
3. ✅ Service worker not blocked by CSP
4. ✅ Manifest served with correct MIME type (`application/manifest+json`)

## References

- [Next PWA Documentation](https://github.com/DuCanhGH/next-pwa)
- [Workbox Documentation](https://developer.chrome.com/docs/workbox)
- [Web App Manifest Spec](https://www.w3.org/TR/appmanifest/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

---

**Implementation Date**: December 28, 2025  
**Package**: `@ducanh2912/next-pwa@^1.0.0`  
**Status**: ✅ Production Ready
