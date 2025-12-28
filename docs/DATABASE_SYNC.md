# Database Sync

## How It Works

Every page load triggers an automatic sync check in the background:

- **Content renders immediately** - no waiting for sync check
- **Newer database found:** Downloads automatically in background, shows sync badge, auto-reloads page with fresh data
- **Already current:** Sync badge disappears quickly, content stays rendered

## Async Architecture

The sync system uses **FastAPI BackgroundTasks** to prevent blocking and timeouts:

1. **Non-blocking initiation:** `/check-and-sync` endpoint returns immediately after starting background task
2. **Status polling:** Frontend polls `/sync-status` every 1 second for progress updates
3. **State tracking:** Thread-safe singleton (`SyncState`) tracks sync status across requests
4. **Timeout protection:** Max 2 minutes of polling prevents infinite loops
5. **Atomic file operations:** Download-then-rename pattern prevents data loss on failure

### Benefits

- ✅ **No API gateway timeouts** - Endpoint returns in <100ms
- ✅ **Worker thread efficiency** - Background tasks don't block request threads
- ✅ **Progress feedback** - Real-time status updates via polling
- ✅ **Scalable** - Can handle large database files (several MB) without issues
- ✅ **Data safety** - Atomic operations preserve existing database on download failures

## Data Safety

The sync implementation uses **atomic file operations** to prevent data loss:

### How It Works

1. **Download to temporary file:** New database is downloaded to `.tmp_kobo_*.sqlite` in the same directory
2. **Verify download:** Checks file exists and is non-empty before proceeding
3. **Atomic rename:** Uses `shutil.move()` which is atomic on POSIX systems
4. **Automatic cleanup:** Temp files are removed if download fails

### Failure Scenarios Handled

- ❌ **Network error during download** → Existing database preserved, temp file cleaned up
- ❌ **B2 outage** → Existing database preserved, no changes made
- ❌ **Disk space exhausted** → Existing database preserved, temp file cleaned up
- ❌ **Incomplete download** → Existing database preserved (empty file check)
- ✅ **Successful download** → Old database atomically replaced with new version

This ensures the application always has a valid database file and never enters a broken state.

## Flow

1. **Page loads** → Header initiates async sync check
2. **Backend checks** timestamps (B2 vs local cache) in background
3. **If newer** → Downloads database in background task
4. **Frontend polls** `/sync-status` for progress (checking → downloading → completed)
5. **On completion** → Auto-reload page to show fresh data
6. **If current** → Hide sync badge, continue

## Sync Badge

Header shows "⟳ Syncing" badge during sync operations with real-time status.

## API Endpoints

### POST `/api/check-and-sync`

Initiates sync check in background. Returns immediately.

**Response:**

```json
{
  "initiated": true,
  "message": "Sync initiated in background",
  "status": "checking"
}
```

### GET `/api/sync-status`

Get current sync status for polling.

**Response:**

```json
{
  "status": "downloading",
  "message": "Downloading database...",
  "progress": 0.0,
  "is_syncing": true,
  "needs_reload": false,
  "file_size_mb": 2.48
}
```

**Status values:** `idle`, `checking`, `downloading`, `completed`, `up_to_date`, `error`

## Implementation Details

- **Frontend:** Header component with polling mechanism (1s intervals, max 120 attempts)
- **Backend:**
  - `SyncState` singleton for thread-safe state management
  - `sync_with_state_tracking()` method with progress updates
  - FastAPI BackgroundTasks for async execution
- **Timestamp Sync:** After download, sets local mtime to match B2 to prevent re-downloads
- **Auto-reload:** Page automatically reloads after successful sync to show fresh data
