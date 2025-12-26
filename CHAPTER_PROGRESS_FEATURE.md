# Sequential Ordering & Location Tracking Feature

## Overview

This feature enhancement provides clear sequential ordering and location tracking for highlights and markups within books. It uses multiple data points from the Kobo database's Bookmark table:

- **OrderingNumber** (extracted from `StartContainerPath`): Primary ordering indicator that increases across the entire book (e.g., "kobo.10.3", "kobo.20.1")
- **ChapterProgress**: Chapter-relative progress (0.0-1.0) showing position within the current chapter
- **SectionTitle**: The HTML file name of the current section/chapter

## Changes Made

### Backend Changes (`highlights-fetch-service/app/services/kobo.py`)

#### 1. Enhanced Highlights Query

- Added `StartContainerPath` and `SectionTitle` fields
- Extracts `OrderingNumber` from `StartContainerPath` for reliable book-wide ordering
- Highlights are enriched with position metadata

```python
def get_highlights(self, book_id: str):
    query = """
        SELECT
            b.BookmarkID, VolumeID, Text, Annotation, DateCreated,
            b.ChapterProgress, b.StartContainerPath,
            c.Title as SectionTitle
        FROM Bookmark b
        LEFT JOIN content c ON c.ContentID = b.ContentID
        WHERE b.VolumeID = ? AND b.Type = 'highlight'
    """
    # Then enriches with OrderingNumber extraction
```

#### 2. Enhanced Markups Query

- Added `ChapterProgress` field to show chapter-relative position
- Extracts `OrderingNumber` from `StartContainerPath` (e.g., "kobo.10.3" → position in book)
- Markups are enriched with multiple position indicators

```python
def get_markups(self, book_id: str):
    query = """
        SELECT
            b.BookmarkID, VolumeID, Text, Annotation,
            b.ExtraAnnotationData, b.DateCreated,
            b.ChapterProgress,
            b.StartContainerPath,
            c.Title as SectionTitle,
            c.adobe_location
        FROM Bookmark b
        LEFT JOIN content c ON c.ContentID = ...
        WHERE b.VolumeID = ? AND b.ExtraAnnotationData IS NOT NULL
    """
    # Then enriches with OrderingNumber and BookPartNumber
```

### Frontend Changes

#### 1. Redesigned Component: `LocationIndicator.tsx`

Created a reusable React component that displays sequential position and location metadata:

**Features:**

- **Sequential number badge** (1, 2, 3, ...) showing reading order
  - Color-coded by position: 🟢 Green (early) → 🟡 Yellow (middle) → 🟣 Purple (late)
- **Section title** display (e.g., "text/part0021_split_002.html")
- **Chapter progress** mini-bar showing % within current chapter
  - Labeled as "Chapter: X%" to clarify it's chapter-relative, not book-absolute
- **Graceful handling** of null/undefined values
- **Responsive design** that works in both light and dark modes

**Usage:**

```tsx
<LocationIndicator
  index={5}
  total={42}
  sectionTitle="Chapter 10: Design"
  chapterProgress={0.37}
  className="mb-2"
/>
// Displays: [5] Section: Chapter 10: Design | Chapter: 37% [===>    ]
```

#### 2. Updated Book Details Page (`app/books/[id]/page.tsx`)

**Highlights Section:**

- Added `LocationIndicator` component showing sequential position (1, 2, 3...)
- Displays section title and chapter progress
- Sorted by `OrderingNumber` (primary) → Date (fallback) for reliable reading order
- Color-coded badges indicate position in sequence

**Markups Section:**

- Added `LocationIndicator` component showing sequential position
- Enhanced sorting logic:
  1. Primary: `OrderingNumber` (most reliable - e.g., "kobo.10.3", "kobo.20.1")
  2. Fallback: `DateCreated`
- Shows position metadata (e.g., "Position: kobo.20.1")
- Location indicator appears at top of each card for easy scanning

## User Experience Improvements

### Before

❌ No indication of reading order or sequence
❌ Items sorted only by date, not book position
❌ Difficult to navigate annotations sequentially
❌ No way to know if annotations are close together or far apart

### After

✅ **Sequential numbering** (1, 2, 3...) shows exact reading order
✅ **Section titles** provide context about where in the book
✅ **Chapter progress** shows relative position within current chapter
✅ **Color-coded badges** for quick visual reference
✅ Sorted by `OrderingNumber` for accurate book-wide positioning
✅ Easy to navigate annotations in the order they appear in the book

## Visual Design

### Location Indicator Layout

```
┌───┐  Section: Chapter 10 | Chapter: 37% [===>    ]
│ 5 │
└───┘
  ↑
  └─ Sequential number (color-coded badge)
```

### Color Scheme (Position in Sequence)

- **Early items (0-33%)**: Green badge - Beginning of annotations
- **Middle items (33-66%)**: Yellow badge - Middle section
- **Late items (66-100%)**: Purple badge - Final annotations

**Note:** The color indicates position in the _sequence of annotations_, not absolute book position, since `ChapterProgress` is chapter-relative.

## Technical Details

### Data Flow

1. **Database** → Kobo SQLite `Bookmark` table contains:
   - `StartContainerPath` (e.g., "span#kobo.20.1") → Extracted to `OrderingNumber`
   - `ChapterProgress` (0.0-1.0, chapter-relative)
   - `ContentID` → Joined to get `SectionTitle`
2. **Backend** → FastAPI service:
   - Fetches bookmark data with JOINs
   - Extracts `OrderingNumber` from `StartContainerPath` using regex
   - Returns enriched data
3. **Frontend** → React component:
   - Sorts by `OrderingNumber` (numeric locale compare) → fallback to Date
   - Assigns sequential indices (1, 2, 3...)
   - Renders badges and metadata
4. **User** → Sees clear sequential ordering and position metadata

### Error Handling

- Missing `OrderingNumber`: Falls back to date-based sorting
- Null `ChapterProgress`: Chapter progress bar is hidden (not shown)
- Invalid values: Component handles gracefully with type checks
- Empty section titles: Only shown if available

## Benefits

1. **Clear Sequential Order**: Users see exact reading order (1, 2, 3...) regardless of creation date
2. **Context Awareness**: Section titles help recall which part of the book
3. **Reliable Sorting**: `OrderingNumber` provides accurate book-wide positioning
4. **Visual Feedback**: Color-coded badges for quick scanning
5. **Chapter Context**: Mini progress bar shows position within current chapter
6. **Export-Friendly**: Position data (`OrderingNumber`) can be used for future export features

## Known Limitations & Future Enhancements

### Current Limitations

- **ChapterProgress is chapter-relative**: Values reset for each chapter (0.2 in Ch 1, then 0.3 in Ch 2)
  - _Mitigation:_ We use `OrderingNumber` for sorting, which is book-wide
  - _Display:_ Chapter progress is labeled "Chapter: X%" to clarify scope
- **OrderingNumber format varies**: Different ebook formats may have different patterns
  - _Mitigation:_ Regex extraction handles common patterns (kobo.X.Y, point(/X/Y:Z))

### Future Enhancements (Optional)

- **Absolute book progress**: Calculate using `ContentID` ordering + `ChapterProgress`
- **Jump to location**: Deep link to specific position in book reader
- **Location filtering**: Filter annotations by section or % range
- **Timeline view**: Visual timeline showing all annotations across the book
- **Chapter names**: Parse actual chapter titles from content metadata
- **Density heatmap**: Show distribution of annotations across book sections
- **Group by chapter**: Collapsible sections grouped by chapter

## Testing

To test the feature:

1. **Start services** (if not already running):
   - Backend: `cd highlights-fetch-service && python3 -m uvicorn main:app --reload`
   - Frontend: `cd library-ui && npm run dev`
2. **Navigate** to any book with highlights or markups
3. **Observe**:
   - ✅ Sequential number badges (1, 2, 3...) in reading order
   - ✅ Color-coded badges (green → yellow → purple)
   - ✅ Section titles displayed
   - ✅ "Chapter: X%" mini progress bars
   - ✅ Items in correct reading order (not just by date)
4. **Verify sorting**: Check that `OrderingNumber` increases (e.g., kobo.10.3 → kobo.20.1)
5. **Test edge cases**: Books without OrderingNumber should still sort by date

## Database Schema Reference

```sql
-- Bookmark table structure (relevant fields)
CREATE TABLE Bookmark (
    BookmarkID TEXT PRIMARY KEY,
    VolumeID TEXT,
    Text TEXT,
    Annotation TEXT,
    ChapterProgress REAL,  -- 0.0 to 1.0, indicates position in book
    DateCreated TEXT,
    Type TEXT              -- 'highlight', 'note', etc.
);
```

---

**Note**: This feature leverages existing Kobo data without requiring any database modifications or external integrations. All location information is already tracked by the Kobo device and stored in the local SQLite database.
