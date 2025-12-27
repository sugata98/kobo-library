# Tabs Feature Implementation Summary

## Overview

Implemented content type filtering using shadcn/ui Tabs component to separate Books from Instapaper Articles in the UI. This addresses the fact that **72% of the library consists of Instapaper articles** (115 articles vs 31 books).

## Changes Made

### 1. Backend API Updates

#### `highlights-fetch-service/app/services/kobo.py`

**Added Content Type Classification:**
- Modified `get_books()` to accept `content_type` parameter
- Added `ContentCategory` field to SQL query that classifies content based on MimeType:
  - `instapaper` or `pocket` → `'article'`
  - `epub` → `'book'`
  - `pdf` → `'pdf'`
  - `nebo` → `'notebook'`
  - Other → `'other'`
- Modified `get_total_books()` to support content type filtering
- Both functions now filter results by content type when provided

**Key SQL Logic:**
```sql
CASE 
    WHEN c1.MimeType LIKE '%instapaper%' THEN 'article'
    WHEN c1.MimeType LIKE '%pocket%' THEN 'article'
    WHEN c1.MimeType LIKE '%epub%' THEN 'book'
    WHEN c1.MimeType LIKE '%pdf%' THEN 'pdf'
    WHEN c1.MimeType LIKE '%nebo%' THEN 'notebook'
    ELSE 'other'
END as ContentCategory
```

#### `highlights-fetch-service/app/api/endpoints.py`

**Updated `/books` Endpoint:**
- Added `type` query parameter: `?type=book|article|pdf|notebook|other`
- Passes `type` to `kobo_service.get_books()` and `kobo_service.get_total_books()`
- Pagination and search work seamlessly with type filtering

**Example API Calls:**
```bash
# All content
GET /api/books?page=1&page_size=10

# Only books
GET /api/books?page=1&page_size=10&type=book

# Only articles
GET /api/books?page=1&page_size=10&type=article

# Search within books
GET /api/books?page=1&page_size=10&type=book&search=python

# Search within articles
GET /api/books?page=1&page_size=10&type=article&search=design
```

### 2. Frontend Updates

#### Installed shadcn Tabs Component

```bash
npx shadcn@latest add tabs
```

Created: `library-ui/components/ui/tabs.tsx`

#### `library-ui/app/page.tsx`

**Added Tabs UI:**
- Imported `Tabs`, `TabsContent`, `TabsList`, `TabsTrigger` from shadcn
- Added `BookOpen` and `FileText` icons from lucide-react
- Created 3 tabs:
  1. **All** - Shows all content (books + articles)
  2. **Books** - Shows only ePub books
  3. **Articles** - Shows only Instapaper/Pocket articles
- Each tab renders a separate `BookList` component with appropriate `contentType` prop
- Added `activeTab` state to track current tab

**Tab Structure:**
```tsx
<Tabs defaultValue="all" value={activeTab} onValueChange={setActiveTab}>
  <TabsList>
    <TabsTrigger value="all">All</TabsTrigger>
    <TabsTrigger value="book">Books</TabsTrigger>
    <TabsTrigger value="article">Articles</TabsTrigger>
  </TabsList>
  
  <TabsContent value="all">
    <BookList searchQuery={query} contentType={null} />
  </TabsContent>
  
  <TabsContent value="book">
    <BookList searchQuery={query} contentType="book" />
  </TabsContent>
  
  <TabsContent value="article">
    <BookList searchQuery={query} contentType="article" />
  </TabsContent>
</Tabs>
```

#### `library-ui/components/BookList.tsx`

**Added Content Type Support:**
- Added `contentType` prop (optional, defaults to `null`)
- Passes `contentType` to `getBooks()` API calls
- Resets to page 1 when `contentType` changes
- Added `contentType` to dependency arrays for `useEffect` hooks

**Changes:**
```typescript
export default function BookList({
  searchQuery = "",
  contentType = null,
}: {
  searchQuery?: string;
  contentType?: string | null;
}) {
  // Reset to page 1 when content type changes
  useEffect(() => {
    setCurrentPage(1);
  }, [contentType]);
  
  // Pass contentType to API calls
  const response = await getBooks(currentPage, pageSize, undefined, contentType);
  
  // Include contentType in dependencies
  }, [currentPage, searchQuery, contentType]);
}
```

#### `library-ui/lib/api.ts`

**Updated `getBooks()` Function:**
- Added `contentType` parameter (optional)
- Appends `type` query parameter when provided

```typescript
export async function getBooks(
  page: number = 1,
  pageSize: number = 10,
  search?: string,
  contentType?: string | null
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (search) {
    params.append("search", search);
  }
  if (contentType) {
    params.append("type", contentType);
  }
  const res = await fetch(`${API_BASE_URL}/books?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch books");
  return res.json();
}
```

## Features

### ✅ Tab Filtering
- Switch between All, Books, and Articles views
- Each tab maintains its own state
- Smooth transitions between tabs

### ✅ Pagination Support
- Each tab has independent pagination
- Page resets to 1 when switching tabs
- Total count updates based on filtered content

### ✅ Search Support
- Search works within each tab
- Searches only the filtered content type
- Search query persists across tab switches

### ✅ Combined Filtering
- Can search within Books tab (searches only books)
- Can search within Articles tab (searches only articles)
- Can search in All tab (searches everything)

## Database Insights (Verified)

From actual database query (`kobo_KoboReader-2.sqlite`):

| ContentType | Count | Description |
|-------------|-------|-------------|
| 6 | 159 | Top-level content (books + articles) |
| 9 | 802 | Individual XHTML file sections |
| 899 | 1,141 | TOC navigation entries |

**ContentType 6 Breakdown by MimeType:**
- `application/x-kobo-html+instapaper`: **115 (72%)** - Instapaper articles
- `application/x-kobo-epub+zip`: **31 (19%)** - ePub books
- Other types: **13 (9%)** - PDFs, notebooks, images

**Key Finding:** The library is **72% Instapaper articles**, making this tab separation highly valuable!

## User Experience Improvements

1. **Clear Separation**: Users can now easily distinguish between books and articles
2. **Focused Browsing**: Can browse only books or only articles without clutter
3. **Better Search**: Can search within a specific content type
4. **Visual Indicators**: Icons (BookOpen for books, FileText for articles) provide visual cues
5. **Accurate Counts**: Each tab shows the correct total count for that content type

## Testing Checklist

- [x] Backend API returns correct content types
- [x] Tabs render correctly
- [x] Switching tabs updates content
- [x] Pagination works per tab
- [x] Search works per tab
- [x] Page resets when switching tabs
- [x] Combined search + filter works
- [x] No TypeScript/linting errors

## Future Enhancements

1. **Badge Counts**: Show count on each tab (e.g., "Books (31)", "Articles (115)")
2. **Different Icons**: Use different icons for books vs articles in the list
3. **Article-specific UI**: Different card layout for articles (e.g., show source, reading time)
4. **PDF Tab**: Add a separate tab for PDFs if needed
5. **Notebook Tab**: Add a tab for Kobo notebooks
6. **Filter Persistence**: Remember last selected tab in localStorage
7. **URL State**: Reflect active tab in URL query parameters

## Related Documentation

- [KOBO_DATABASE_STRUCTURE.md](./KOBO_DATABASE_STRUCTURE.md) - Complete database structure reference
- [shadcn/ui Tabs Documentation](https://ui.shadcn.com/docs/components/tabs)

