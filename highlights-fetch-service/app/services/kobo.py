import sqlite3
from typing import List, Dict, Any, Optional
from app.core.config import settings

class KoboService:
    def __init__(self, db_path: str = settings.LOCAL_DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.text_factory = bytes 
        return conn

    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            value = row[idx]
            col_name = col[0]
            
            if value is None:
                d[col_name] = None
                continue
                
            if isinstance(value, bytes):
                if col_name == 'ExtraAnnotationData':
                    try:
                        d[col_name] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        d[col_name] = value.hex()
                else:
                    try:
                        d[col_name] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        d[col_name] = value.hex()
            else:
                d[col_name] = value
        return d

    def get_books(self, limit: Optional[int] = None, offset: Optional[int] = None, search: Optional[str] = None, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        # Deduplicate books by Title + Author
        # For duplicate books, pick the one with the highest progress or most recent date
        # Sort: Books with progress first (descending), then alphabetically
        query = """
            SELECT 
                c1.ContentID,
                c1.Title, 
                c1.Attribution as Author, 
                MAX(c1.DateCreated) as DateCreated, 
                MAX(c1.___PercentRead) as ___PercentRead,
                c1.ImageUrl,
                c1.ISBN,
                c1.MimeType,
                CASE 
                    WHEN c1.MimeType LIKE '%instapaper%' THEN 'article'
                    WHEN c1.MimeType LIKE '%pocket%' THEN 'article'
                    WHEN c1.MimeType LIKE '%epub%' THEN 'book'
                    WHEN c1.MimeType LIKE '%pdf%' THEN 'pdf'
                    WHEN c1.MimeType LIKE '%nebo%' THEN 'notebook'
                    ELSE 'other'
                END as ContentCategory
            FROM content c1
            WHERE c1.ContentType = '6' 
            AND (c1.BookID IS NULL OR c1.BookID = '')
            AND c1.ContentID = (
                SELECT c2.ContentID
                FROM content c2
                WHERE c2.ContentType = '6'
                AND (c2.BookID IS NULL OR c2.BookID = '')
                AND c2.Title = c1.Title
                AND (c2.Attribution = c1.Attribution OR (c2.Attribution IS NULL AND c1.Attribution IS NULL))
                ORDER BY c2.___PercentRead DESC, c2.DateCreated DESC
                LIMIT 1
            )
        """
        
        # Add content type filter if provided
        search_params = []
        if content_type:
            query += """
            AND (
                CASE 
                    WHEN c1.MimeType LIKE '%instapaper%' THEN 'article'
                    WHEN c1.MimeType LIKE '%pocket%' THEN 'article'
                    WHEN c1.MimeType LIKE '%epub%' THEN 'book'
                    WHEN c1.MimeType LIKE '%pdf%' THEN 'pdf'
                    WHEN c1.MimeType LIKE '%nebo%' THEN 'notebook'
                    ELSE 'other'
                END
            ) = ?
            """
            search_params.append(content_type)
        
        # Add search filter if provided (before GROUP BY)
        if search:
            search_term = f"%{search.lower()}%"
            query += """
            AND (LOWER(c1.Title) LIKE ? OR LOWER(c1.Attribution) LIKE ?)
            """
            search_params.extend([search_term, search_term])
        
        query += """
            GROUP BY c1.Title, c1.Attribution
            ORDER BY 
                CASE WHEN MAX(c1.___PercentRead) > 0 THEN 0 ELSE 1 END,
                MAX(c1.___PercentRead) DESC,
                LOWER(c1.Title) ASC
        """
        
        # Build parameters list: search params first, then limit/offset
        params = list(search_params) if search_params else []
        
        # Add LIMIT and OFFSET as bound parameters
        if limit is not None and offset is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([int(limit), int(offset)])
        elif limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        
        # Execute with all parameters
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        books = cursor.fetchall()
        conn.close()
        
        return books
    
    def get_total_books(self, search: Optional[str] = None, content_type: Optional[str] = None) -> int:
        """Get the total count of unique books, optionally filtered by search and content type"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT COUNT(DISTINCT c1.Title || COALESCE(c1.Attribution, '')) as total
            FROM content c1
            WHERE c1.ContentType = '6' 
            AND (c1.BookID IS NULL OR c1.BookID = '')
            AND c1.ContentID = (
                SELECT c2.ContentID
                FROM content c2
                WHERE c2.ContentType = '6'
                AND (c2.BookID IS NULL OR c2.BookID = '')
                AND c2.Title = c1.Title
                AND (c2.Attribution = c1.Attribution OR (c2.Attribution IS NULL AND c1.Attribution IS NULL))
                ORDER BY c2.___PercentRead DESC, c2.DateCreated DESC
                LIMIT 1
            )
        """
        
        # Add content type filter if provided
        search_params = []
        if content_type:
            query += """
            AND (
                CASE 
                    WHEN c1.MimeType LIKE '%instapaper%' THEN 'article'
                    WHEN c1.MimeType LIKE '%pocket%' THEN 'article'
                    WHEN c1.MimeType LIKE '%epub%' THEN 'book'
                    WHEN c1.MimeType LIKE '%pdf%' THEN 'pdf'
                    WHEN c1.MimeType LIKE '%nebo%' THEN 'notebook'
                    ELSE 'other'
                END
            ) = ?
            """
            search_params.append(content_type)
        
        # Add search filter if provided
        if search:
            search_term = f"%{search.lower()}%"
            query += """
            AND (LOWER(c1.Title) LIKE ? OR LOWER(c1.Attribution) LIKE ?)
            """
            search_params.extend([search_term, search_term])
        
        if search_params:
            cursor.execute(query, search_params)
        else:
            cursor.execute(query)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get a single book by ContentID"""
        conn = self.get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        query = """
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
            AND ContentID = ?
            LIMIT 1
        """
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()
        conn.close()
        return book

    def get_highlights(self, book_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        query = """
            SELECT 
                b.BookmarkID, 
                b.VolumeID, 
                b.Text, 
                b.Annotation, 
                b.DateCreated, 
                b.ChapterProgress,
                b.StartContainerPath,
                c.Title as SectionTitle,
                c.VolumeIndex,
                c.ContentID,
                (
                    SELECT ch.Title
                    FROM content ch
                    WHERE ch.BookID = c.BookID
                    AND ch.Depth = 1
                    AND ch.ContentType = '899'
                    AND SUBSTR(ch.ContentID, INSTR(ch.ContentID, 'part'), 8) = 
                        SUBSTR(c.ContentID, INSTR(c.ContentID, 'part'), 8)
                    LIMIT 1
                ) as ChapterName
            FROM Bookmark b
            LEFT JOIN content c ON c.ContentID = b.ContentID
            WHERE b.VolumeID = ? AND b.Type = 'highlight'
            ORDER BY b.DateCreated
        """
        cursor.execute(query, (book_id,))
        highlights = cursor.fetchall()
        
        # Calculate true chapter-wide progress for each highlight (before closing connection)
        highlights = self._calculate_chapter_progress(highlights, book_id, conn)
        
        conn.close()
        
        # Enrich with ordering number
        for highlight in highlights:
            highlight['OrderingNumber'] = self._extract_ordering_number(highlight.get('StartContainerPath', ''))
        
        return highlights
    
    def get_markups(self, book_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        # Enhanced query to get metadata like section title, ordering info, and chapter name
        query = """
            SELECT 
                b.BookmarkID, 
                b.VolumeID, 
                b.Text, 
                b.Annotation, 
                b.ExtraAnnotationData, 
                b.DateCreated,
                b.ChapterProgress,
                b.StartContainerPath,
                c.Title as SectionTitle,
                c.VolumeIndex,
                c.ContentID,
                c.adobe_location,
                (
                    SELECT ch.Title
                    FROM content ch
                    WHERE ch.BookID = c.BookID
                    AND ch.Depth = 1
                    AND ch.ContentType = '899'
                    AND SUBSTR(ch.ContentID, INSTR(ch.ContentID, 'part'), 8) = 
                        SUBSTR(c.ContentID, INSTR(c.ContentID, 'part'), 8)
                    LIMIT 1
                ) as ChapterName
            FROM Bookmark b
            LEFT JOIN content c ON c.ContentID = (
                SELECT ContentID FROM Bookmark WHERE BookmarkID = b.BookmarkID
            )
            WHERE b.VolumeID = ? AND b.ExtraAnnotationData IS NOT NULL
            ORDER BY b.ChapterProgress, b.DateCreated
        """
        cursor.execute(query, (book_id,))
        all_bookmarks = cursor.fetchall()
        
        # Calculate true chapter-wide progress for each markup (before closing connection)
        all_bookmarks = self._calculate_chapter_progress(all_bookmarks, book_id, conn)
        
        conn.close()
        
        # Enrich with ordering number
        for markup in all_bookmarks:
            markup['OrderingNumber'] = self._extract_ordering_number(markup.get('StartContainerPath', ''))
            markup['BookPartNumber'] = self._extract_book_part_number(markup.get('adobe_location', ''))
        
        return all_bookmarks
    
    def _extract_ordering_number(self, start_container_path: str) -> Optional[str]:
        """Extract ordering number from StartContainerPath (e.g., 'span#kobo.16.2' -> 'kobo.16.2')"""
        if not start_container_path:
            return None
        
        # Handle bytes if needed
        if isinstance(start_container_path, bytes):
            start_container_path = start_container_path.decode('utf-8', errors='ignore')
        
        # Match span#kobo.16.2 or point(/1/2:3)
        import re
        kobo_match = re.match(r'^span#([\w.]+)$', start_container_path)
        pdf_match = re.match(r'point\((\/[\d/]+:\d+)\)', start_container_path)
        
        if kobo_match:
            return kobo_match.group(1).replace(':', '.').replace('/', '.')
        if pdf_match:
            return pdf_match.group(1).replace(':', '.').replace('/', '.')
        
        return None
    
    def _extract_book_part_number(self, adobe_location: str) -> Optional[str]:
        """Extract book part number from adobe_location"""
        if not adobe_location:
            return None
        
        if isinstance(adobe_location, bytes):
            adobe_location = adobe_location.decode('utf-8', errors='ignore')
        
        if adobe_location:
            parts = adobe_location.split('/')
            if parts:
                last_part = parts[-1]
                return last_part.split('.')[0]
        
        return None
    
    def _calculate_chapter_progress(self, bookmarks: List[Dict[str, Any]], book_id: str, conn) -> List[Dict[str, Any]]:
        """
        Calculate true chapter-wide progress for bookmarks.
        ChapterProgress from Kobo is actually section-relative (resets for each split file).
        This calculates the true progress across the entire chapter.
        """
        try:
            cursor = conn.cursor()
            
            # Group bookmarks by chapter (using part number from ContentID)
            chapter_ranges = {}  # {part_number: (min_volume_index, max_volume_index)}
            
            for bookmark in bookmarks:
                content_id = bookmark.get('ContentID')
                if not content_id:
                    continue
                
                # Convert bytes to string if needed
                if isinstance(content_id, bytes):
                    content_id = content_id.decode('utf-8', errors='ignore')
                
                # Extract part number (e.g., "part0023" from the ContentID)
                import re
                part_match = re.search(r'part\d+', content_id)
                if not part_match:
                    continue
                
                part_number = part_match.group()
                
                # If we haven't seen this chapter yet, query its range
                if part_number not in chapter_ranges:
                    cursor.execute("""
                        SELECT MIN(VolumeIndex) as MinIndex, MAX(VolumeIndex) as MaxIndex
                        FROM content
                        WHERE BookID = ? 
                        AND ContentID LIKE ?
                        AND Depth = 0
                    """, (book_id, f'%{part_number}%'))
                    
                    result = cursor.fetchone()
                    if result and result.get('MinIndex') is not None and result.get('MaxIndex') is not None:
                        chapter_ranges[part_number] = (result['MinIndex'], result['MaxIndex'])
            
            # Now calculate true progress for each bookmark
            for bookmark in bookmarks:
                content_id = bookmark.get('ContentID')
                section_progress = bookmark.get('ChapterProgress')
                volume_index = bookmark.get('VolumeIndex')
                
                if not content_id or section_progress is None or volume_index is None:
                    bookmark['TrueChapterProgress'] = None
                    continue
                
                # Convert bytes to string if needed
                if isinstance(content_id, bytes):
                    content_id = content_id.decode('utf-8', errors='ignore')
                
                # Extract part number
                import re
                part_match = re.search(r'part\d+', content_id)
                if not part_match or part_match.group() not in chapter_ranges:
                    bookmark['TrueChapterProgress'] = None
                    continue
                
                part_number = part_match.group()
                chapter_start, chapter_end = chapter_ranges[part_number]
                total_sections = chapter_end - chapter_start + 1
                
                # Safety check
                if total_sections <= 0:
                    bookmark['TrueChapterProgress'] = section_progress
                    continue
                
                # Calculate true chapter progress
                # (current section position + progress within section) / total sections
                section_position = volume_index - chapter_start
                true_progress = (section_position + section_progress) / total_sections
                
                # Clamp between 0 and 1
                true_progress = max(0.0, min(1.0, true_progress))
                
                bookmark['TrueChapterProgress'] = true_progress
            
            return bookmarks
        except Exception as e:
            # Log the error and return bookmarks without TrueChapterProgress
            import traceback
            print(f"Error calculating chapter progress: {e}")
            print(traceback.format_exc())
            # Set TrueChapterProgress to None for all bookmarks
            for bookmark in bookmarks:
                bookmark['TrueChapterProgress'] = None
            return bookmarks

kobo_service = KoboService()
