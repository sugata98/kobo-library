from fastapi import APIRouter, HTTPException, Response, Query, Depends
from fastapi.responses import StreamingResponse
from app.services.b2 import b2_service, b2_covers_service
from app.services.kobo import kobo_service
from app.services.cover_service import cover_service
from app.core.config import settings
from app.core.auth import require_auth
import os
import logging
import urllib.parse
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sync")
def sync_data(username: str = Depends(require_auth)):
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
              search: str = Query(None, description="Search query for title or author"),
              type: str = Query(None, description="Filter by content type: 'book', 'article', 'pdf', 'notebook', 'other'"),
              username: str = Depends(require_auth)):
    # Auto-sync if database doesn't exist
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
        books = kobo_service.get_books(limit=page_size, offset=offset, search=search, content_type=type)
        # Get total count of matching books (with optional search filter and content type)
        total_books = kobo_service.get_total_books(search=search, content_type=type)
        total_pages = (total_books + page_size - 1) // page_size if total_books > 0 else 1
        
        logger.info(f"Retrieved {len(books)} items (type={type}, page {page}, total: {total_books})")
        
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
def get_book_highlights(book_id: str, username: str = Depends(require_auth)):
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
def get_book_markups(book_id: str, username: str = Depends(require_auth)):
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

@router.get("/books/{book_id:path}/cover")
def get_book_cover(
    book_id: str, 
    title: str = Query(None, description="Book title"),
    author: str = Query(None, description="Book author"),
    isbn: str = Query(None, description="Book ISBN-13"),
    image_url: str = Query(None, description="Book ImageUrl from database")
):
    """
    Get book cover image with smart fallback strategy.
    
    Priority order:
    1. ImageUrl from Kobo database (for articles/books with embedded covers)
    2. bookcover-api (Goodreads) - best quality for published books
    3. Open Library - fallback
    4. Google Books - fallback
    
    Example: /api/books/{book_id}/cover?title=Clean Code&author=Robert Martin&isbn=9780132350884
    """
    # Decode URL-encoded parameters
    if title:
        title = urllib.parse.unquote(title)
    if author:
        author = urllib.parse.unquote(author)
    if isbn:
        isbn = urllib.parse.unquote(isbn)
    if image_url:
        image_url = urllib.parse.unquote(image_url)
    
    logger.info(f"Fetching cover for book_id: {book_id}, title: {title}, author: {author}, isbn: {isbn}, image_url: {image_url}")
    
    # Use provided parameters or fetch from database as fallback
    if not title or not image_url:
        # Fallback: Get from database if parameters not provided
        try:
            if os.path.exists(settings.LOCAL_DB_PATH):
                decoded_book_id = urllib.parse.unquote(book_id)
                book = kobo_service.get_book_by_id(decoded_book_id)
                if not book:
                    book = kobo_service.get_book_by_id(book_id)
                
                if book:
                    title = book.get('Title') if not title else title
                    author = book.get('Author') if not author else author
                    isbn = book.get('ISBN') if not isbn else isbn
                    image_url = book.get('ImageUrl') if not image_url else image_url
                    
                    # Handle bytes if needed
                    if isinstance(title, bytes):
                        title = title.decode('utf-8', errors='ignore')
                    if isinstance(author, bytes):
                        author = author.decode('utf-8', errors='ignore')
                    if isinstance(isbn, bytes):
                        isbn = isbn.decode('utf-8', errors='ignore')
                    if isinstance(image_url, bytes):
                        image_url = image_url.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.debug(f"Could not get book info from database: {e}")
    
    if not title:
        raise HTTPException(
            status_code=400, 
            detail="Title is required. Pass 'title' as query parameter: /api/books/{book_id}/cover?title=Book Title"
        )
    
    # PRIORITY 1: Try ImageUrl from Kobo database first (for articles/embedded covers)
    if image_url and image_url.strip():
        try:
            logger.info(f"📚 Found ImageUrl in database: {image_url[:100]}...")
            # Try to fetch the image from the URL
            img_response = requests.get(image_url, timeout=10)
            if img_response.status_code == 200 and img_response.content and len(img_response.content) > 0:
                # Detect content type from response
                content_type = img_response.headers.get('content-type', 'image/jpeg')
                logger.info(f"✅ Successfully fetched cover from ImageUrl for: {title}")
                
                # Return with Cache-Control headers for browser caching
                return Response(
                    content=img_response.content, 
                    media_type=content_type,
                    headers={
                        "Cache-Control": "public, max-age=2592000, immutable",  # 30 days
                        "Content-Length": str(len(img_response.content))
                    }
                )
            else:
                logger.warning(f"⚠️  ImageUrl returned status {img_response.status_code}, falling back to external APIs")
        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch ImageUrl: {e}, falling back to external APIs")
    
    # PRIORITY 2-4: Fallback to external APIs with B2 caching (bookcover-api, Open Library, Google Books)
    try:
        # Set B2 covers service on cover_service for caching
        cover_service.b2_service = b2_covers_service
        
        # First, try to get from B2 cache with streaming (fastest, most efficient)
        cache_stream = cover_service.get_from_b2_cache_stream(title, author, isbn, image_url)
        if cache_stream:
            logger.info(f"✅ Streaming cover from B2 cache for: {title}")
            return StreamingResponse(
                cache_stream,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=2592000, immutable",  # 30 days
                }
            )
        
        # If not in cache, fetch from external APIs
        cover_result = cover_service.fetch_cover(title, author, isbn, image_url)
        if cover_result:
            image_bytes, content_type = cover_result
            logger.info(f"Found cover from online API for: {title}")
            
            # Return with Cache-Control headers for browser caching
            return Response(
                content=image_bytes, 
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=2592000, immutable",  # 30 days
                    "Content-Length": str(len(image_bytes))
                }
            )
        else:
            logger.warning(f"No cover found in online APIs for: {title} by {author or 'Unknown'}")
    except Exception as e:
        logger.error(f"Error fetching cover for {title}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cover: {str(e)}"
        )
    
    # If no cover found from any source
    raise HTTPException(
        status_code=404, 
        detail=f"Cover image not found for: {title}"
    )

@router.get("/books/{book_id:path}")
def get_book_details(book_id: str, username: str = Depends(require_auth)):
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
def get_markup_svg(markup_id: str, username: str = Depends(require_auth)):
    # Based on logs, the path is 'kobo/markups/{markup_id}.svg'
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
def get_markup_jpg(markup_id: str, username: str = Depends(require_auth)):
    # The JPG file should have the same ID as the SVG
    # Based on leldr's tool, they match by BookmarkID
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
