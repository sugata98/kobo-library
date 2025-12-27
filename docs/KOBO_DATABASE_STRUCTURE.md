# Kobo Database Structure Reference

## Overview

The Kobo e-reader stores all reading data in a SQLite database called `KoboReader.sqlite`. This document outlines the database structure based on the current implementation and provides insights into differentiating between books and articles.

## Key Tables

### 1. `content` Table

The primary table containing all content items (books, articles, chapters, sections).

#### Key Fields

| Field            | Type    | Description                                                                                |
| ---------------- | ------- | ------------------------------------------------------------------------------------------ |
| `ContentID`      | TEXT    | Unique identifier for the content (e.g., `file:///mnt/onboard/kepub/BookTitle.kepub.epub`) |
| `ContentType`    | TEXT    | Type of content (see ContentType values below)                                             |
| `MimeType`       | TEXT    | MIME type of the content (e.g., `application/x-kobo-epub+zip`)                             |
| `BookID`         | TEXT    | Parent book identifier (NULL for top-level books)                                          |
| `Title`          | TEXT    | Title of the content                                                                       |
| `Attribution`    | TEXT    | Author name(s)                                                                             |
| `ImageUrl`       | TEXT    | Path to cover image (e.g., `file:///mnt/onboard/.kobo-images/{hash}.png`)                  |
| `ISBN`           | TEXT    | ISBN-13 identifier (when available)                                                        |
| `DateCreated`    | TEXT    | Creation/addition date                                                                     |
| `___PercentRead` | REAL    | Reading progress (0.0 to 1.0)                                                              |
| `Depth`          | INTEGER | Hierarchy depth (0 = section, 1 = chapter, etc.)                                           |
| `VolumeIndex`    | INTEGER | Sequential index for ordering sections                                                     |
| `adobe_location` | TEXT    | Adobe DRM location identifier                                                              |

#### ContentType Values

Based on **actual database inspection** (queried from kobo_KoboReader-2.sqlite):

| ContentType | Count | Description                                       | Depth | Usage in Readr                                                              |
| ----------- | ----- | ------------------------------------------------- | ----- | --------------------------------------------------------------------------- |
| `6`         | 159   | **Top-level books AND articles** (parent items)   | -     | ✅ Used for book/article list (filtered by `BookID IS NULL OR BookID = ''`) |
| `9`         | 802   | **Individual file sections** (XHTML pages)        | 0     | Not used - represents individual files within ePub structure                |
| `899`       | 1,141 | **TOC entries with readable titles** (navigation) | 1     | ✅ Used for chapter name extraction (filtered by `Depth = 1`)               |

**ContentType Breakdown:**

**ContentType 6 (159 records)** - MimeType Distribution:

- `application/x-kobo-html+instapaper`: **115 records** (72%) - **INSTAPAPER ARTICLES** 📰
- `application/x-kobo-epub+zip`: **31 records** (19%) - Standard Kobo ePub books 📚
- `application/vnd.myscript.nebo+raw`: 4 records - Kobo notebooks
- `application/octet-stream`: 4 records - Generic files
- `image/png`: 3 records - Image files
- `application/vnd.myscript.nebo+text`: 1 record - Notebook file
- `application/pdf`: 1 record - PDF document

**Important Discovery:** Your library is **72% Instapaper articles** (not Pocket)! You have 115 articles vs 31 books.

**ContentType 9 (802 records):**

- Individual XHTML files within books (e.g., `cover.xhtml`, `chapter01.xhtml`)
- Has `BookID` pointing to parent book
- Depth = 0 (file level)
- MimeType: `application/xhtml+xml`

**ContentType 899 (1,141 records):**

- Table of Contents entries with human-readable titles
- Has `BookID` pointing to parent book
- Depth = 1 (navigation level)
- MimeType: `application/x-kobo-epub+zip`
- These are what appear in the Kobo's reading navigation

### 2. `Bookmark` Table

Contains all highlights, annotations, and bookmarks.

#### Key Fields

| Field                 | Type | Description                                         |
| --------------------- | ---- | --------------------------------------------------- |
| `BookmarkID`          | TEXT | Unique identifier for the bookmark                  |
| `VolumeID`            | TEXT | References the book's ContentID                     |
| `ContentID`           | TEXT | References the specific section/chapter             |
| `Type`                | TEXT | Type of bookmark (e.g., `highlight`, `dogear`)      |
| `Text`                | TEXT | Highlighted text content                            |
| `Annotation`          | TEXT | User's annotation/note                              |
| `ExtraAnnotationData` | BLOB | Additional annotation data (for scribbles/drawings) |
| `DateCreated`         | TEXT | Creation timestamp                                  |
| `ChapterProgress`     | REAL | Progress within the section (0.0 to 1.0)            |
| `StartContainerPath`  | TEXT | XPath-like location (e.g., `span#kobo.16.2`)        |

## Differentiating Books from Articles

### Current Approach

The current implementation in `kobo.py` does **not** explicitly differentiate between books and articles. It treats all `ContentType = '6'` entries with `BookID IS NULL` as "books."

**Critical Insight:** Research confirms that **both books AND Pocket articles use ContentType 6**. Articles are NOT a separate ContentType (like 9 or 10). The differentiation must be done using other fields, primarily `MimeType`.

### Potential Differentiation Methods

Based on Kobo's ecosystem and common patterns, here are ways to potentially distinguish books from articles:

#### 1. **MimeType Field** (Most Reliable - VERIFIED)

Different content types have different MIME types (verified from actual database):

| MimeType                             | Content Type                         | Count in Your DB |
| ------------------------------------ | ------------------------------------ | ---------------- |
| `application/x-kobo-html+instapaper` | **Instapaper articles** ⭐ CONFIRMED | 115 (72%)        |
| `application/x-kobo-epub+zip`        | Standard Kobo ePub books             | 31 (19%)         |
| `application/pdf`                    | PDF documents                        | 1 (1%)           |
| `application/vnd.myscript.nebo+raw`  | Kobo notebook (raw)                  | 4 (3%)           |
| `application/vnd.myscript.nebo+text` | Kobo notebook (text)                 | 1 (1%)           |
| `application/octet-stream`           | Generic files                        | 4 (3%)           |
| `image/png`                          | Image files                          | 3 (2%)           |
| `application/x-kobo-html+pocket`     | **Pocket articles** (NOT in your DB) | 0                |
| `application/x-kobo-kepub+zip`       | Kobo-enhanced ePub (NOT in your DB)  | 0                |

**Key Finding:** Your articles are from **Instapaper**, not Pocket!

**Recommendation:** Check MimeType for:

- `%instapaper%` → Instapaper articles 📰
- `%pocket%` → Pocket articles 📰
- `%epub%` → ePub books 📚
- `%pdf%` → PDF documents 📄

```sql
-- Query to identify Instapaper articles (VERIFIED QUERY)
SELECT ContentID, Title, Attribution, MimeType
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
AND MimeType LIKE '%instapaper%';

-- Alternative: Query for any articles (Instapaper OR Pocket)
SELECT ContentID, Title, Attribution, MimeType
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
AND (MimeType LIKE '%instapaper%' OR MimeType LIKE '%pocket%');
```

#### 2. **ContentID Pattern** (Moderately Reliable)

Articles from Pocket or web sources may have distinctive ContentID patterns:

- **Books:** `file:///mnt/onboard/kepub/BookTitle.kepub.epub`
- **Pocket Articles:** May contain `pocket` in the path or have HTTP/HTTPS URLs
- **Web Articles:** May start with `http://` or `https://`

```sql
-- Query to identify web/Pocket articles by ContentID
SELECT ContentID, Title, Attribution
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
AND (
    ContentID LIKE '%pocket%'
    OR ContentID LIKE 'http%'
);
```

#### 3. **ISBN Field** (Partial Indicator)

- **Books:** Usually have an ISBN (though not always)
- **Articles:** Typically do NOT have an ISBN

```sql
-- Query to identify likely articles (no ISBN)
SELECT ContentID, Title, Attribution, ISBN
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
AND (ISBN IS NULL OR ISBN = '');
```

**Limitation:** Many books also lack ISBN data, so this is not definitive.

#### 4. **ImageUrl Field** (Weak Indicator)

- **Books:** Often have cover images stored in `.kobo-images/`
- **Articles:** May have embedded images or external URLs

```sql
-- Query to check ImageUrl patterns
SELECT ContentID, Title, ImageUrl
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
AND ImageUrl IS NOT NULL;
```

#### 5. **Attribution (Author) Field** (Weak Indicator)

- **Books:** Usually have author names
- **Articles:** May have website names or be empty

This is highly unreliable as many articles have authors and some books lack attribution.

## Recommended Implementation

### Option 1: Add a "Type" Filter Based on MimeType

Modify the `get_books()` query to include a type classification:

```python
def get_books(self, content_type: Optional[str] = None):
    query = """
        SELECT
            c1.ContentID,
            c1.Title,
            c1.Attribution as Author,
            c1.MimeType,
            c1.ISBN,
            CASE
                WHEN c1.MimeType LIKE '%instapaper%' THEN 'article'
                WHEN c1.MimeType LIKE '%pocket%' THEN 'article'
                WHEN c1.MimeType LIKE '%pdf%' THEN 'pdf'
                WHEN c1.MimeType LIKE '%nebo%' THEN 'notebook'
                WHEN c1.MimeType LIKE '%epub%' THEN 'book'
                ELSE 'unknown'
            END as ContentCategory
        FROM content c1
        WHERE c1.ContentType = '6'
        AND (c1.BookID IS NULL OR c1.BookID = '')
    """

    # Add filter if content_type is specified
    if content_type:
        query += " AND ContentCategory = ?"
```

### Option 2: Add Separate Endpoints

Create separate API endpoints:

- `/api/books` - Only books (exclude Pocket articles)
- `/api/articles` - Only Pocket articles
- `/api/library` - Everything (current behavior)

### Option 3: Add a Query Parameter

Add a `type` query parameter to the existing `/api/books` endpoint:

```
GET /api/books?type=book
GET /api/books?type=article
GET /api/books?type=all (default)
```

## Database Query Examples

### Get All Books (Excluding Articles)

```sql
SELECT
    ContentID,
    Title,
    Attribution as Author,
    DateCreated,
    ___PercentRead,
    ImageUrl,
    ISBN
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
AND MimeType LIKE '%epub%'
ORDER BY Title;
```

### Get Only Articles (Instapaper/Pocket)

```sql
SELECT
    ContentID,
    Title,
    Attribution as Author,
    DateCreated,
    ___PercentRead,
    ImageUrl,
    MimeType
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
AND (MimeType LIKE '%instapaper%' OR MimeType LIKE '%pocket%')
ORDER BY DateCreated DESC;
```

### Get All Content with Category Classification

```sql
SELECT
    ContentID,
    Title,
    Attribution as Author,
    MimeType,
    CASE
        WHEN MimeType LIKE '%instapaper%' THEN 'Instapaper Article'
        WHEN MimeType LIKE '%pocket%' THEN 'Pocket Article'
        WHEN MimeType LIKE '%epub%' THEN 'ePub Book'
        WHEN MimeType LIKE '%pdf%' THEN 'PDF'
        WHEN MimeType LIKE '%nebo%' THEN 'Notebook'
        ELSE 'Other'
    END as ContentCategory
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
ORDER BY ContentCategory, Title;
```

### Get Content Statistics

```sql
SELECT
    CASE
        WHEN MimeType LIKE '%pocket%' THEN 'Pocket Article'
        WHEN MimeType LIKE '%pdf%' THEN 'PDF'
        WHEN MimeType LIKE '%epub%' THEN 'ePub Book'
        ELSE 'Other'
    END as ContentType,
    COUNT(*) as Count
FROM content
WHERE ContentType = '6'
AND (BookID IS NULL OR BookID = '')
GROUP BY ContentType;
```

## Notes and Observations

**Database Structure (Confirmed from actual database query):**

1. **Only 3 ContentType values exist**: 6 (159 records), 9 (802 records), and 899 (1,141 records)
2. **ContentType 6 includes BOTH books and articles** - they share the same ContentType
   - 115 Instapaper articles (72%)
   - 31 ePub books (19%)
   - 9 other items (notebooks, PDFs, images)
3. **ContentType 9** - Individual XHTML file sections within books (e.g., cover.xhtml, chapter files) with Depth=0
4. **ContentType 899** - TOC entries with readable chapter titles and Depth=1 (used for navigation)
5. **No ContentType 10 (newspapers)** or Pocket articles in your database

**Implementation Details:**

6. **BookID NULL/empty** ensures we only get parent entries (ContentType 6), not sub-sections
7. **MimeType is THE differentiator** between books and Instapaper articles (since they share ContentType 6)
8. **The current implementation treats everything as "books"** - no distinction is made, but **72% are actually Instapaper articles**
9. **ImageUrl from database** is used as the highest priority for cover images (especially useful for articles with embedded covers)
10. **Depth field differentiates TOC entries**: Depth=0 (ContentType 9 - file sections), Depth=1 (ContentType 899 - navigation titles)

**Key Takeaway:**

- External documentation about Kobo databases may differ from your specific database version/structure
- Your library uses **Instapaper**, not Pocket, for article syncing
- You have **3.7x more articles than books** (115 vs 31)

## Related Documentation

- [KOBO_COVERS.md](./KOBO_COVERS.md) - Cover image handling
- [BOOKCOVER_API_INTEGRATION.md](./BOOKCOVER_API_INTEGRATION.md) - External cover API integration
- [highlights-fetch-service/app/services/kobo.py](./highlights-fetch-service/app/services/kobo.py) - Current implementation

## Future Enhancements

1. **Add content type classification** to the API response
2. **Add filtering by content type** in the UI
3. **Different UI treatment** for articles vs. books (e.g., different icons, layouts)
4. **Separate statistics** for books vs. articles in the dashboard
5. **Export functionality** that preserves the distinction
