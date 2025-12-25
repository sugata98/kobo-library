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

    def get_books(self, limit: Optional[int] = None, offset: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
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
                c1.ISBN
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
        
        # Add search filter if provided (before GROUP BY)
        search_params = []
        if search:
            search_term = f"%{search.lower()}%"
            query += """
            AND (LOWER(c1.Title) LIKE ? OR LOWER(c1.Attribution) LIKE ?)
            """
            search_params = [search_term, search_term]
        
        query += """
            GROUP BY c1.Title, c1.Attribution
            ORDER BY 
                CASE WHEN MAX(c1.___PercentRead) > 0 THEN 0 ELSE 1 END,
                MAX(c1.___PercentRead) DESC,
                LOWER(c1.Title) ASC
        """
        
        if limit is not None and offset is not None:
            query += f" LIMIT {limit} OFFSET {offset}"
        elif limit is not None:
            query += f" LIMIT {limit}"
        
        if search_params:
            cursor.execute(query, search_params)
        else:
            cursor.execute(query)
        books = cursor.fetchall()
        conn.close()
        
        return books
    
    def get_total_books(self) -> int:
        """Get the total count of unique books"""
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
            SELECT BookmarkID, VolumeID, Text, Annotation, DateCreated, ChapterProgress
            FROM Bookmark
            WHERE VolumeID = ? AND Type = 'highlight'
        """
        cursor.execute(query, (book_id,))
        highlights = cursor.fetchall()
        conn.close()
        return highlights
    
    def get_markups(self, book_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        # Enhanced query to get metadata like section title, ordering info
        query = """
            SELECT 
                b.BookmarkID, 
                b.VolumeID, 
                b.Text, 
                b.Annotation, 
                b.ExtraAnnotationData, 
                b.DateCreated,
                b.StartContainerPath,
                c.Title as SectionTitle,
                c.adobe_location
            FROM Bookmark b
            LEFT JOIN content c ON c.ContentID = (
                SELECT ContentID FROM Bookmark WHERE BookmarkID = b.BookmarkID
            )
            WHERE b.VolumeID = ? AND b.ExtraAnnotationData IS NOT NULL
            ORDER BY b.DateCreated
        """
        cursor.execute(query, (book_id,))
        all_bookmarks = cursor.fetchall()
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

kobo_service = KoboService()
