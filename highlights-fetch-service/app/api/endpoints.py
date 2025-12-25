from fastapi import APIRouter, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from app.services.b2 import b2_service
from app.services.kobo import kobo_service
from app.services.cover_service import cover_service
from app.core.config import settings
import os
import logging
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sync")
def sync_data():
    """
    Syncs KoboReader.sqlite from B2 storage to the configured local database path.
    
    Attempts a direct download of "kobo/KoboReader.sqlite" to settings.LOCAL_DB_PATH; if that fails it lists the bucket and downloads the first file whose name ends with "KoboReader.sqlite". Creates the local directory if needed.
    
    Returns:
        dict: {"message": "Database synced successfully"} on success.
    
    Raises:
        HTTPException: with status code 500 if the sync or download process fails.
    """
    try:
        local_path = settings.LOCAL_DB_PATH
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        logger.info(f"Attempting to download KoboReader.sqlite from bucket {settings.B2_BUCKET_NAME}...")
        
        try:
            b2_service.download_file("kobo/KoboReader.sqlite", local_path)
            logger.info("Successfully downloaded kobo/KoboReader.sqlite")
        except Exception as e:
            logger.warning(f"Direct download of 'kobo/KoboReader.sqlite' failed: {e}. Searching bucket...")
            files = b2_service.list_files()
            file_names = [f.file_name for f, _ in files]
            sqlite_file = next((f for f in file_names if f.endswith('KoboReader.sqlite')), None)
            
            if sqlite_file:
                logger.info(f"Found '{sqlite_file}', downloading...")
                b2_service.download_file(sqlite_file, local_path)
            else:
                raise Exception(f"Could not find KoboReader.sqlite in bucket. content: {file_names[:10]}")

        return {"message": "Database synced successfully"}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books")
def get_books(page: int = Query(1, ge=1, description="Page number (1-indexed)"), 
              page_size: int = Query(10, ge=1, le=100, description="Number of books per page"),
              search: str = Query(None, description="Search query for title or author")):
    # Auto-sync if database doesn't exist
    """
              Retrieve a paginated list of books with optional title/author search.
              
              If the local KoboReader.sqlite database is missing, attempts an automatic sync from B2 before querying.
              When `search` is provided, `total` is computed across all matching records (not just the returned page).
              Pagination is 1-indexed.
              
              Returns:
                  dict: {
                      "books": list of book records,
                      "pagination": {
                          "page": int,
                          "page_size": int,
                          "total": int,
                          "total_pages": int
                      }
                  }
              
              Raises:
                  HTTPException: If the database cannot be found or auto-sync/querying fails.
              """
              if not os.path.exists(settings.LOCAL_DB_PATH):
        logger.info("Database not found, attempting auto-sync...")
        try:
            local_path = settings.LOCAL_DB_PATH
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            try:
                b2_service.download_file("kobo/KoboReader.sqlite", local_path)
                logger.info("Auto-sync successful: downloaded KoboReader.sqlite")
            except Exception as e:
                logger.warning(f"Direct download failed: {e}. Searching bucket...")
                files = b2_service.list_files()
                file_names = [f.file_name for f, _ in files]
                sqlite_file = next((f for f in file_names if f.endswith('KoboReader.sqlite')), None)
                
                if sqlite_file:
                    logger.info(f"Found '{sqlite_file}', downloading...")
                    b2_service.download_file(sqlite_file, local_path)
                else:
                    raise HTTPException(status_code=404, detail="Database not found in B2. Please ensure KoboReader.sqlite is synced to B2.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auto-sync failed: {e}")
            raise HTTPException(status_code=500, detail=f"Auto-sync failed: {str(e)}")
    
    try:
        offset = (page - 1) * page_size
        books = kobo_service.get_books(limit=page_size, offset=offset, search=search)
        # For search, get total count of matching books
        if search:
            # Get all matching books to count (without limit)
            all_matching = kobo_service.get_books(limit=None, offset=None, search=search)
            total_books = len(all_matching)
        else:
            total_books = kobo_service.get_total_books()
        total_pages = (total_books + page_size - 1) // page_size if total_books > 0 else 1
        
        logger.info(f"Retrieved {len(books)} books (page {page}, total: {total_books})")
        
        return {
            "books": books,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_books,
                "total_pages": total_pages
            }
        }
    except Exception as e:
        logger.error(f"Failed to get books: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# IMPORTANT: More specific routes must come BEFORE the generic route
# Otherwise FastAPI will match the generic route first

@router.get("/books/{book_id:path}/highlights")
def get_book_highlights(book_id: str):
    """
    Retrieve highlights for a book identified by `book_id`.
    
    Attempts to fetch highlights using the provided `book_id`. If no highlights are found, retries with the URL-decoded `book_id` when it differs from the original.
    
    Parameters:
        book_id (str): Book identifier from the request path; may be URL-encoded.
    
    Returns:
        list: Highlights for the specified book.
    
    Raises:
        HTTPException: 404 if the local database is missing.
        HTTPException: 500 for unexpected errors while fetching highlights.
    """
    if not os.path.exists(settings.LOCAL_DB_PATH):
        raise HTTPException(status_code=404, detail="Database not found. Please sync first.")
    
    logger.info(f"Fetching highlights for book_id: {book_id}")
    try:
        highlights = kobo_service.get_highlights(book_id)
        if not highlights:
            decoded_id = urllib.parse.unquote(book_id)
            if decoded_id != book_id:
                highlights = kobo_service.get_highlights(decoded_id)
        return highlights
    except Exception as e:
        logger.error(f"Error fetching highlights for {book_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books/{book_id:path}/markups")
def get_book_markups(book_id: str):
    """
    Retrieve markups associated with a book identifier.
    
    Parameters:
        book_id (str): Book identifier (ContentID). Supports URL-encoded values; the function will retry with a URL-decoded ID if no markups are found for the original.
    
    Returns:
        list: A list of markup records for the specified book; an empty list if no markups are found.
    
    Raises:
        HTTPException: 404 if the local database is not present.
        HTTPException: 500 if an unexpected error occurs while fetching markups.
    """
    if not os.path.exists(settings.LOCAL_DB_PATH):
        raise HTTPException(status_code=404, detail="Database not found. Please sync first.")
    
    logger.info(f"Fetching markups for book_id: {book_id}")
    try:
        markups = kobo_service.get_markups(book_id)
        if not markups:
             decoded_id = urllib.parse.unquote(book_id)
             if decoded_id != book_id:
                 markups = kobo_service.get_markups(decoded_id)
        return markups
    except Exception as e:
        logger.error(f"Error fetching markups for {book_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books/{book_id:path}")
def get_book_details(book_id: str):
    """
    Retrieve detailed metadata for a book by its ID, trying a URL-decoded ID first and falling back to the original ID.
    
    Parameters:
        book_id (str): The book identifier from the request path; may be URL-encoded.
    
    Returns:
        dict: The book record retrieved from the local Kobo database (metadata fields as returned by the service).
    
    Raises:
        HTTPException: 404 if the local database is missing or the book is not found.
        HTTPException: 500 if an unexpected error occurs while fetching book details.
    """
    if not os.path.exists(settings.LOCAL_DB_PATH):
        raise HTTPException(status_code=404, detail="Database not found. Please sync first.")
    
    logger.info(f"Fetching book details for book_id: {book_id}")
    try:
        decoded_id = urllib.parse.unquote(book_id)
        book = kobo_service.get_book_by_id(decoded_id)
        if not book:
            # Try with original ID if decoded didn't work
            if decoded_id != book_id:
                book = kobo_service.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
        return book
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching book details for {book_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/markup/{markup_id}/svg")
def get_markup_svg(markup_id: str):
    # Based on logs, the path is 'kobo/markups/{markup_id}.svg'
    """
    Retrieve an SVG image for a markup by searching known B2 storage paths.
    
    Parameters:
        markup_id (str): Identifier of the markup (filename without path or extension).
    
    Returns:
        Response: HTTP response containing the SVG bytes with content type "image/svg+xml".
    
    Raises:
        HTTPException: with status 404 if the SVG file cannot be found in B2.
    """
    possible_paths = [
        f"kobo/markups/{markup_id}.svg",
        f"markups/{markup_id}.svg",
        f"{markup_id}.svg"
    ]
    
    logger.info(f"Fetching SVG for markup_id: {markup_id}")
    
    for path in possible_paths:
        try:
            content = b2_service.get_file_content(path)
            logger.info(f"Found SVG at {path}")
            return Response(content=content, media_type="image/svg+xml")
        except Exception as e:
            continue
            
    raise HTTPException(status_code=404, detail="SVG file not found in B2")

@router.get("/markup/{markup_id}/jpg")
def get_markup_jpg(markup_id: str):
    # The JPG file should have the same ID as the SVG
    # Based on leldr's tool, they match by BookmarkID
    """
    Return a streaming JPEG image for a markup by attempting several common storage paths.
    
    Parameters:
        markup_id (str): Identifier of the markup used to build possible file paths (e.g., bookmark or markup ID).
    
    Returns:
        StreamingResponse: A streaming response that yields JPEG image bytes with content type `image/jpeg`.
    
    Raises:
        HTTPException: 404 if no JPEG file for the given markup_id is found in storage.
    """
    possible_paths = [
        f"kobo/markups/{markup_id}.jpg",
        f"markups/{markup_id}.jpg",
        f"{markup_id}.jpg"
    ]
    
    logger.info(f"Fetching JPG for markup_id: {markup_id}")
    
    for path in possible_paths:
        try:
            # Use streaming for large files to reduce memory usage
            stream = b2_service.get_file_stream(path)
            logger.info(f"Found JPG at {path}")
            return StreamingResponse(stream, media_type="image/jpeg")
        except Exception as e:
            continue
            
    raise HTTPException(status_code=404, detail="JPG file not found in B2")

@router.get("/book/{book_id}/cover")
def get_book_cover(
    book_id: str, 
    title: str = Query(None, description="Book title"),
    author: str = Query(None, description="Book author")
):
    """
    Retrieve a book cover image using the provided title and optional author, or by falling back to the local Kobo database.
    
    If `title` is omitted, the function attempts to read Title and Attribution from the local KoboReader.sqlite using `book_id`. Raises HTTPException 400 if a title cannot be determined. On success returns the image bytes with the appropriate content type; if no image is found in the online APIs, raises HTTPException 404. On unexpected errors, raises HTTPException 500.
    
    Parameters:
        book_id (str): ContentID used to look up title/author in the local database when `title` is not provided.
        title (str, optional): Book title provided as a query parameter; URL-decoded before use.
        author (str, optional): Book author provided as a query parameter; URL-decoded before use.
    
    Returns:
        Response: HTTP response containing the image bytes and the matching media type (e.g., image/jpeg or image/png).
    """
    # Decode URL-encoded parameters
    if title:
        title = urllib.parse.unquote(title)
    if author:
        author = urllib.parse.unquote(author)
    
    logger.info(f"Fetching cover for book_id: {book_id}, title: {title}, author: {author}")
    
    # Use provided title/author or fetch from database as fallback
    if not title:
        # Fallback: Get from database if title not provided
        try:
            if os.path.exists(settings.LOCAL_DB_PATH):
                decoded_book_id = urllib.parse.unquote(book_id)
                conn = kobo_service.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT Title, Attribution FROM content WHERE ContentID = ?", (decoded_book_id,))
                result = cursor.fetchone()
                if not result:
                    cursor.execute("SELECT Title, Attribution FROM content WHERE ContentID = ?", (book_id,))
                    result = cursor.fetchone()
                conn.close()
                
                if result:
                    title = result[0]
                    author = result[1] if not author else author
                    
                    # Handle bytes if needed
                    if isinstance(title, bytes):
                        title = title.decode('utf-8', errors='ignore')
                    if isinstance(author, bytes):
                        author = author.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.debug(f"Could not get book info from database: {e}")
    
    if not title:
        raise HTTPException(
            status_code=400, 
            detail="Title is required. Pass 'title' as query parameter: /api/book/{book_id}/cover?title=Book Title"
        )
    
    # Fetch cover from free online APIs
    try:
        cover_result = cover_service.fetch_cover(title, author)
        if cover_result:
            image_bytes, content_type = cover_result
            logger.info(f"Found cover from online API for: {title}")
            return Response(content=image_bytes, media_type=content_type)
        else:
            logger.warning(f"No cover found in online APIs for: {title} by {author or 'Unknown'}")
    except Exception as e:
        logger.error(f"Error fetching cover for {title}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cover: {str(e)}"
        )
    
    # If no cover found from APIs
    raise HTTPException(
        status_code=404, 
        detail=f"Cover image not found in online APIs for: {title}"
    )