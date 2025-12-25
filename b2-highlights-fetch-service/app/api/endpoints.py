from fastapi import APIRouter, HTTPException, Response
from app.services.b2 import b2_service
from app.services.kobo import kobo_service
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
def get_books():
    if not os.path.exists(settings.LOCAL_DB_PATH):
        raise HTTPException(status_code=404, detail="Database not found. Please sync first.")
    try:
        return kobo_service.get_books()
    except Exception as e:
        logger.error(f"Failed to get books: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books/{book_id:path}/highlights")
def get_book_highlights(book_id: str):
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

@router.get("/markup/{markup_id}/svg")
def get_markup_svg(markup_id: str):
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
def get_markup_jpg(markup_id: str):
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
            content = b2_service.get_file_content(path)
            logger.info(f"Found JPG at {path}")
            return Response(content=content, media_type="image/jpeg")
        except Exception as e:
            continue
            
    raise HTTPException(status_code=404, detail="JPG file not found in B2")
