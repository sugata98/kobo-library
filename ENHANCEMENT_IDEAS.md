# Enhancement Ideas for Kobo Library

Based on comprehensive database schema analysis, here are feature suggestions organized by priority and feasibility.

## 🎨 **HIGH PRIORITY - Quick Wins**

### 1. **Highlight Color Categorization**

- **Data Available**: `Bookmark.Color` field (values: 0, 1, 3)
- **Feature**: Display highlights with color-coded borders/backgrounds matching Kobo's color system
- **Benefits**:
  - Visual differentiation between highlight types
  - Users often color-code by importance/category
  - Filter/group by color
- **Implementation**: Update `LocationIndicator` component with color-based styling

### 2. **Reading Timeline**

- **Data Available**:
  - `Bookmark.DateCreated` (when highlight was made)
  - `content.DateLastRead` (last opened)
  - `content.DateAdded` (when book was added)
- **Feature**: Timeline view showing when highlights/markups were created
- **Benefits**:
  - Track reading progress over time
  - Rediscover old highlights
  - See reading patterns (morning vs evening, weekdays vs weekends)
- **Implementation**: New timeline view with date-based filtering

### 3. **Series Tracking**

- **Data Available**:
  - `content.Series` (series name)
  - `content.SeriesNumber` (book number in series)
  - `content.SeriesID`
- **Feature**: Group books by series, show reading order
- **Benefits**:
  - Organize multi-book series
  - Track series reading progress
  - Quick navigation between series books
- **Implementation**: New series view in BookList component

### 4. **Enhanced Book Metadata Display**

- **Data Available**:
  - `content.Publisher`
  - `content.Subtitle`
  - `content.Language`
  - `content.WordCount`
  - `content.___NumPages`
- **Feature**: Rich book detail cards with all metadata
- **Benefits**: Professional, informative UI
- **Implementation**: Expand BookDetails page with metadata section

## 📊 **MEDIUM PRIORITY - Valuable Analytics**

### 5. **Reading Activity Dashboard**

- **Data Available**: `Event` table with:
  - `EventType` (various reading events)
  - `FirstOccurrence`, `LastOccurrence`
  - `EventCount`
- **Feature**: Dashboard showing:
  - Books recently read (`content.DateLastRead`)
  - Reading sessions from `Event` table
  - Most highlighted books
  - Highlight/markup density per book
- **Benefits**: Understand reading habits, gamification potential

### 6. **Highlight Density Visualization**

- **Data Available**: Highlights per chapter (already calculated)
- **Feature**: Visual heatmap showing which chapters have most highlights
- **Benefits**:
  - Quickly identify key chapters
  - See engagement patterns
  - Find "important" sections at a glance
- **Implementation**: Add chapter-level summary view with bar chart or heatmap

### 7. **Search & Filter System**

- **Data Available**: All bookmark text, dates, chapters
- **Feature**:
  - Full-text search across all highlights
  - Filter by date range
  - Filter by chapter
  - Filter by color
  - Sort by date/position/chapter
- **Benefits**: Find specific highlights quickly
- **Implementation**: Search bar with advanced filter UI

### 8. **Recently Read Books**

- **Data Available**:
  - `Activity` table (Type='RecentBook')
  - `content.DateLastRead`
- **Feature**: "Continue Reading" section on home page
- **Benefits**: Quick access to current books
- **Implementation**: New component on home page

## 🚀 **ADVANCED FEATURES - High Impact**

### 9. **Bookmark Context Display**

- **Data Available**: `Bookmark.ContextString` (currently empty, but could be populated)
- **Alternative**: Use `StartContainerPath`, `StartOffset`, `EndOffset` to extract context from EPUB
- **Feature**: Show text before/after highlight for context
- **Benefits**: Understand highlight context without re-reading
- **Implementation**: Backend EPUB parsing + frontend display

### 10. **Highlight Annotations & Notes**

- **Data Available**: `Bookmark.Annotation` (already captured)
- **Feature**:
  - Display user notes attached to highlights
  - Count highlights with notes
  - Filter by "has notes"
- **Benefits**: Surface user's thoughts alongside highlights
- **Implementation**: Show annotation text in highlight cards

### 11. **Reading Statistics Page**

- **Data Available**: Aggregate from Bookmarks, Events, Activity
- **Feature**: Stats dashboard with:
  - Total highlights/markups across all books
  - Highlights per book (bar chart)
  - Most highlighted chapters
  - Reading activity calendar (GitHub-style contribution graph)
  - Average highlights per day/week/month
- **Benefits**: Gamification, user engagement
- **Implementation**: New statistics page with charts (recharts/chart.js)

### 12. **Export Features**

- **Data Available**: All highlight/markup data
- **Feature**: Export to:
  - Markdown (organized by chapter)
  - PDF (formatted reading notes)
  - JSON (for other tools)
  - CSV (for analysis)
- **Benefits**: Use highlights outside the app
- **Implementation**: Backend export endpoints + download buttons

## 🎯 **NICE TO HAVE - Polish**

### 13. **Book Tags/Collections**

- **Data Available**: `content.BookshelfTags`, `Shelf` + `ShelfContent` tables
- **Feature**: Custom collections/tags for organizing books
- **Benefits**: User-defined organization beyond series
- **Implementation**: Tag management UI + filtering

### 14. **Duplicate Highlight Detection**

- **Data Available**: Bookmark text
- **Feature**: Detect and merge similar/identical highlights
- **Benefits**: Clean up accidental duplicates
- **Implementation**: Text similarity comparison algorithm

### 15. **Reading Goal Tracking**

- **Data Available**: `content.___PercentRead`, reading dates
- **Feature**: Set and track reading goals (books/month, pages/day)
- **Benefits**: Motivation, habit building
- **Implementation**: Goal setting UI + progress tracking

### 16. **Highlight Sharing**

- **Data Available**: Bookmark text + chapter info
- **Feature**: Generate shareable images/cards with quotes
- **Benefits**: Social engagement, sharing insights
- **Implementation**: Image generation service (canvas/puppeteer)

### 17. **Dark/Light Mode Toggle**

- **Current**: Tailwind dark mode classes present
- **Feature**: User-controlled theme toggle
- **Benefits**: Better UX, accessibility
- **Implementation**: React context + localStorage persistence

## 📋 **Technical Improvements**

### 18. **Caching Layer**

- **Problem**: Database queries on every page load
- **Solution**: Redis/in-memory cache for book list, highlights
- **Benefits**: Faster load times, reduced database load

### 19. **Pagination**

- **Problem**: Large books with 100+ highlights load slowly
- **Solution**: Paginate highlights/markups (20-50 per page)
- **Benefits**: Better performance, faster initial render

### 20. **Real-time Database Sync**

- **Current**: Manual sync from B2
- **Feature**: Auto-sync on schedule or webhook from KoSync
- **Benefits**: Always up-to-date data
- **Implementation**: Cron job or webhook listener

---

## 🎯 **Recommended Implementation Order**

**Phase 1: Visual Enhancements (Week 1)**

1. Highlight color categorization (#1)
2. Enhanced book metadata (#4)
3. Highlight annotations display (#10)

**Phase 2: Discovery Features (Week 2)**  
4. Reading timeline (#2) 5. Search & filter system (#7) 6. Recently read books (#8)

**Phase 3: Organization (Week 3)** 7. Series tracking (#3) 8. Highlight density visualization (#6) 9. Reading activity dashboard (#5)

**Phase 4: Advanced Features (Week 4+)** 10. Export features (#12) 11. Reading statistics page (#11) 12. User preferences & settings (#17)

---

## 🔍 **Database Query Examples**

### Get Highlights with Colors

```sql
SELECT
    b.Text,
    b.Color,
    b.Annotation,
    b.DateCreated,
    c.Title as ChapterName
FROM Bookmark b
LEFT JOIN content c ON c.ContentID = b.ContentID
WHERE b.VolumeID = ? AND b.Type = 'highlight'
ORDER BY b.DateCreated DESC;
```

### Get Reading Timeline

```sql
SELECT
    DATE(DateCreated) as Date,
    COUNT(*) as HighlightCount
FROM Bookmark
WHERE VolumeID = ? AND Type = 'highlight'
GROUP BY DATE(DateCreated)
ORDER BY Date DESC;
```

### Get Series Books

```sql
SELECT
    BookTitle,
    Series,
    SeriesNumber,
    ___PercentRead,
    DateLastRead
FROM content
WHERE Series IS NOT NULL
AND Depth = 0
ORDER BY Series, CAST(SeriesNumber AS REAL);
```

### Get Highlight Density by Chapter

```sql
SELECT
    c.Title as ChapterName,
    COUNT(b.BookmarkID) as HighlightCount,
    MIN(b.DateCreated) as FirstHighlight,
    MAX(b.DateCreated) as LastHighlight
FROM Bookmark b
LEFT JOIN content c ON SUBSTR(c.ContentID, INSTR(c.ContentID, 'part'), 8) =
                       SUBSTR(b.ContentID, INSTR(b.ContentID, 'part'), 8)
WHERE b.VolumeID = ?
AND b.Type = 'highlight'
AND c.Depth = 1
GROUP BY c.Title
ORDER BY HighlightCount DESC;
```

---

## 💡 **Quick Prototyping Suggestions**

For rapid prototyping, prioritize features that:

1. **Use existing data** (no schema changes)
2. **Frontend-only** (no backend changes)
3. **High visual impact** (immediately noticeable)

**Best candidates:**

- ✅ Highlight colors (#1) - just styling changes
- ✅ Timeline view (#2) - use existing DateCreated
- ✅ Metadata display (#4) - just UI changes
- ✅ Annotations (#10) - data already available

**Avoid initially:**

- ❌ Real-time sync (#20) - complex infrastructure
- ❌ Context extraction (#9) - requires EPUB parsing
- ❌ Sharing images (#16) - needs image generation service
