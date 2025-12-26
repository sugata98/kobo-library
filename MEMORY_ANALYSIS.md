# Memory Usage Analysis for 512MB Server

## Current Memory Breakdown

### Base Application (~100-150MB)
- **Python runtime**: ~30-50MB
- **FastAPI/Uvicorn**: ~20-30MB
- **Dependencies** (b2sdk, requests, sqlite3): ~30-50MB
- **Application code**: ~10-20MB

### Database Operations (~10-50MB)
- **SQLite database file**: Stored on disk, not fully loaded into memory
- **Query results**: Only loaded rows are in memory (typically <10MB for book lists)
- **SQLite overhead**: ~5-10MB for connection pooling and caching

### Image Fetching (Variable - **POTENTIAL ISSUE**)
- **Cover images**: 50-200KB per image
- **Concurrent requests**: If 10 users load covers simultaneously = 500KB-2MB
- **Temporary buffers**: Image data held in memory during fetch/response

### B2 Downloads (~20-50MB peak)
- **Database download**: Temporary buffer during download
- **Markup images**: JPG/SVG files loaded into memory when serving

## Potential Memory Issues

### ⚠️ Risk Areas:
1. **Concurrent cover fetches**: Multiple users requesting covers simultaneously
2. **Large database**: If KoboReader.sqlite is >100MB, download uses significant memory
3. **Markup images**: JPG files can be large (500KB-2MB each)
4. **No connection limits**: Default uvicorn can handle many concurrent requests

## Recommendations for 512MB Server

### ✅ Should Work Fine If:
- Database size < 50MB
- < 5-10 concurrent users
- Cover fetching happens client-side (which it does now!)

### ⚠️ Optimizations Needed:
1. **Limit uvicorn workers**: Use single worker to reduce memory
2. **Stream large responses**: Don't load entire images into memory
3. **Add connection limits**: Prevent too many concurrent requests
4. **Monitor memory**: Add logging to track usage

## Current Status

**Good news**: Since covers are now fetched **client-side** (from browser), the backend doesn't need to fetch cover images anymore! This significantly reduces memory pressure.

**Remaining memory usage**:
- Base app: ~100-150MB
- Database operations: ~10-50MB
- Markup images (only when viewing): ~1-5MB per request
- **Total typical**: ~150-200MB
- **Peak (with markups)**: ~250-300MB

## Verdict: ✅ Should work on 512MB

With covers fetched client-side, you should be fine on 512MB. However, consider:
- Limiting concurrent requests
- Monitoring memory usage
- Using a single uvicorn worker

