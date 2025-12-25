import requests
import logging
import urllib.parse
from typing import Optional, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)

class CoverService:
    """Service to fetch book covers from free online APIs"""
    
    @staticmethod
    def fetch_from_open_library(title: str, author: Optional[str] = None) -> Optional[bytes]:
        """
        Search Open Library for the given title (and optional author) and return the book cover image bytes if found.
        
        Searches Open Library's search API for the title and author, then attempts to retrieve a cover image using the result's `cover_i` (cover ID) and, if that fails, the first available ISBN. Returns the raw image bytes when a valid image is fetched; returns `None` if no cover is found or an error occurs.
        
        Parameters:
            title (str): Book title to search for. Leading/trailing whitespace is ignored.
            author (Optional[str]): Optional author name to include in the search.
        
        Returns:
            Optional[bytes]: Image bytes of the cover when found, `None` otherwise.
        """
        try:
            # Build search query - clean and encode
            clean_title = title.strip() if title else ""
            if not clean_title:
                return None
                
            query = clean_title
            if author:
                clean_author = author.strip() if author else ""
                if clean_author:
                    query = f"{clean_title} {clean_author}"
            
            # Search for the book
            search_url = "https://openlibrary.org/search.json"
            params = {
                "q": query,
                "limit": 1
            }
            
            logger.debug(f"Searching Open Library for: {query}")
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("docs") or len(data["docs"]) == 0:
                return None
            
            # Get the first result
            book = data["docs"][0]
            
            # Try to get cover image
            # Open Library uses cover_i (cover ID) or ISBN
            cover_id = book.get("cover_i")
            isbn = None
            
            # Try to get ISBN-13 or ISBN-10
            if "isbn" in book:
                isbns = book["isbn"]
                if isbns:
                    isbn = isbns[0] if isinstance(isbns, list) else isbn
            
            # Try cover ID first (most reliable)
            if cover_id:
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                img_response = requests.get(cover_url, timeout=10)
                if img_response.status_code == 200 and img_response.content and len(img_response.content) > 0:
                    logger.info(f"Found cover from Open Library (cover_id: {cover_id})")
                    return img_response.content
                else:
                    logger.debug(f"Open Library cover image request failed: status={img_response.status_code}, content_length={len(img_response.content) if img_response.content else 0}")
            
            # Fallback to ISBN
            if isbn:
                cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
                img_response = requests.get(cover_url, timeout=10)
                if img_response.status_code == 200 and img_response.content and len(img_response.content) > 0:
                    logger.info(f"Found cover from Open Library (ISBN: {isbn})")
                    return img_response.content
                else:
                    logger.debug(f"Open Library ISBN cover request failed: status={img_response.status_code}, content_length={len(img_response.content) if img_response.content else 0}")
            
            return None
            
        except Exception as e:
            logger.error(f"Open Library API error: {e}", exc_info=True)
            return None
    
    @staticmethod
    def fetch_from_google_books(title: str, author: Optional[str] = None) -> Optional[bytes]:
        """
        Fetch a book cover image from Google Books using the provided title and optional author.
        
        Attempts to find the best-matching volume and retrieve an image by trying available image sizes in descending preference. Returns the raw image bytes when a valid image is obtained, or None if no cover could be retrieved.
         
        Returns:
            image_bytes (Optional[bytes]): Raw image data if found, None otherwise.
        """
        try:
            # Build search query - clean and encode
            clean_title = title.strip() if title else ""
            if not clean_title:
                return None
                
            query = f"intitle:{clean_title}"
            if author:
                clean_author = author.strip() if author else ""
                if clean_author:
                    query = f"{query}+inauthor:{clean_author}"
            
            # Search for the book
            search_url = "https://www.googleapis.com/books/v1/volumes"
            params = {
                "q": query,
                "maxResults": 1
            }
            
            logger.debug(f"Searching Google Books for: {query}")
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("items") or len(data["items"]) == 0:
                return None
            
            # Get the first result
            volume = data["items"][0]
            volume_info = volume.get("volumeInfo", {})
            
            # Try to get cover image
            image_links = volume_info.get("imageLinks", {})
            
            # Try different image sizes (large is best)
            for size in ["large", "medium", "small", "thumbnail", "smallThumbnail"]:
                cover_url = image_links.get(size)
                if cover_url:
                    # Replace http with https
                    cover_url = cover_url.replace("http://", "https://")
                    img_response = requests.get(cover_url, timeout=10)
                    if img_response.status_code == 200 and img_response.content and len(img_response.content) > 0:
                        logger.info(f"Found cover from Google Books (size: {size})")
                        return img_response.content
                    else:
                        logger.debug(f"Google Books cover request failed for size {size}: status={img_response.status_code}, content_length={len(img_response.content) if img_response.content else 0}")
            
            return None
            
        except Exception as e:
            logger.error(f"Google Books API error: {e}", exc_info=True)
            return None
    
    @staticmethod
    def fetch_cover(title: str, author: Optional[str] = None) -> Optional[Tuple[bytes, str]]:
        """
        Locate a book cover image by querying Open Library and Google Books.
        
        Searches in this order: Open Library with the provided title, Open Library with a simplified title (special characters removed), Google Books with the provided title, and Google Books with the simplified title. Logs progress and returns on the first successful image retrieval.
        
        Parameters:
            title (str): The book title to search for. Leading/trailing whitespace is ignored.
            author (Optional[str]): Optional author name to refine the search.
        
        Returns:
            Optional[Tuple[bytes, str]]: A tuple (image_bytes, content_type) where `image_bytes` is the raw image data and `content_type` is the MIME type (set to "image/jpeg") if a cover is found; `None` if no cover could be retrieved.
        """
        # Clean title and author
        clean_title = title.strip() if title else ""
        clean_author = author.strip() if author else None
        
        if not clean_title:
            logger.warning("No title provided for cover fetch")
            return None
        
        logger.info(f"Fetching cover for: '{clean_title}' by {clean_author or 'Unknown'}")
        
        # Try Open Library first (usually faster)
        cover_data = CoverService.fetch_from_open_library(clean_title, clean_author)
        if cover_data:
            return (cover_data, "image/jpeg")
        
        # Try with simplified title (remove special characters, quotes, etc.)
        simplified_title = CoverService._simplify_title(clean_title)
        if simplified_title != clean_title:
            logger.debug(f"Trying simplified title: '{simplified_title}'")
            cover_data = CoverService.fetch_from_open_library(simplified_title, clean_author)
            if cover_data:
                return (cover_data, "image/jpeg")
        
        # Fallback to Google Books
        cover_data = CoverService.fetch_from_google_books(clean_title, clean_author)
        if cover_data:
            return (cover_data, "image/jpeg")
        
        # Try Google Books with simplified title
        if simplified_title != clean_title:
            cover_data = CoverService.fetch_from_google_books(simplified_title, clean_author)
            if cover_data:
                return (cover_data, "image/jpeg")
        
        logger.warning(f"No cover found for: '{clean_title}' by {clean_author or 'Unknown'}")
        return None
    
    @staticmethod
    def _simplify_title(title: str) -> str:
        """
        Simplify a book title by removing punctuation and normalizing whitespace.
        
        Removes characters that are not word characters, spaces, or hyphens, replaces them with spaces, collapses consecutive whitespace into single spaces, and trims leading/trailing whitespace.
        
        Parameters:
            title (str): The original title to simplify.
        
        Returns:
            str: The simplified title.
        """
        import re
        # Remove common special characters but keep basic punctuation
        simplified = re.sub(r'[^\w\s-]', ' ', title)
        # Collapse multiple spaces
        simplified = re.sub(r'\s+', ' ', simplified)
        return simplified.strip()

cover_service = CoverService()
