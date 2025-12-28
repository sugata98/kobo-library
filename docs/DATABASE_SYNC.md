# Database Sync

## How It Works

Every page load triggers an automatic sync check in the background:

- **Content renders immediately** - no waiting for sync check
- **Newer database found:** Downloads automatically, shows sync badge, auto-reloads page with fresh data
- **Already current:** Sync badge disappears quickly, content stays rendered

## Flow

1. Page loads → Header initiates sync check
2. Backend compares timestamps (B2 vs local cache)
3. If newer → Download database, auto-reload page
4. If current → Hide sync badge, continue

## Sync Badge

Header shows "⟳ Syncing" badge during sync operations.

## Implementation

- **Frontend:** Header component manages sync on mount
- **Backend:** Compares B2 upload timestamp vs local file mtime
- **Timestamp Sync:** After download, sets local mtime to match B2 to prevent loops
- **Auto-reload:** Page automatically reloads after successful sync to show fresh data
