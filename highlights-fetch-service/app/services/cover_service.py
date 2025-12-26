import requests
import logging
import urllib.parse
import hashlib
from typing import Optional, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)

class CoverService:
    """Service to fetch book covers from APIs with B2 caching"""
    
    BOOKCOVER_API_BASE_URL = "https://bookcover.longitood.com"
    
    def __init__(self, b2_service=None):
        """Initialize with optional B2 service for caching"""
        self.b2_service = b2_service
    
    def _generate_cache_key(self, title: str, author: Optional[str] = None, isbn: Optional[str] = None, image_url: Optional[str] = None) -> str:
        """
        Generate a unique cache key for a book cover.
        No prefix needed since we're using a dedicated covers bucket.
        """
        # Use ISBN if available (most reliable)
        if isbn and isbn.strip():
            clean_isbn = isbn.strip().replace("-", "").replace(" ", "")
            return f"by-isbn/{clean_isbn}.jpg"
        
        # Use image_url hash if available
        if image_url and image_url.strip():
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            return f"by-imageurl/{url_hash}.jpg"
        
        # Fallback to title+author hash
        cache_str = f"{title.lower().strip()}_{author.lower().strip() if author else ''}"
        title_hash = hashlib.md5(cache_str.encode()).hexdigest()
        return f"by-title/{title_hash}.jpg"
    
    def get_from_b2_cache(self, title: str, author: Optional[str] = None, isbn: Optional[str] = None, image_url: Optional[str] = None) -> Optional[bytes]:
        """Check if cover exists in B2 cache and return it"""
        if not self.b2_service:
            return None
        
        try:
            cache_key = self._generate_cache_key(title, author, isbn, image_url)
            
            logger.info(f"💾 Checking B2 covers cache: {cache_key}")
            cover_bytes = self.b2_service.get_file_content(cache_key)
            logger.info(f"✅ Found cover in B2 cache for: {title}")
            return cover_bytes
        except Exception as e:
            logger.debug(f"B2 cache miss or error: {e}")
            return None
    
    def store_to_b2_cache(self, image_bytes: bytes, title: str, author: Optional[str] = None, isbn: Optional[str] = None, image_url: Optional[str] = None) -> bool:
        """Store cover image to B2 cache"""
        if not self.b2_service or not image_bytes:
            return False
        
        try:
            cache_key = self._generate_cache_key(title, author, isbn, image_url)
            
            logger.info(f"💾 Storing to B2 covers cache: {cache_key}")
            
            # Upload to B2
            from io import BytesIO
            file_stream = BytesIO(image_bytes)
            self.b2_service.upload_file(file_stream, cache_key, content_type="image/jpeg")
            
            logger.info(f"✅ Stored cover to B2 cache for: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to store cover to B2 cache: {e}")
            return False
    
    @staticmethod
    def fetch_from_bookcover_api(title: str, author: Optional[str] = None, isbn: Optional[str] = None) -> Optional[bytes]:
        """
        Fetch cover from bookcover-api (https://github.com/w3slley/bookcover-api)
        This API fetches covers from Goodreads and provides high-quality images.
        Returns image bytes or None if not found
        """
        try:
            # Strategy 1: Try ISBN-13 first if available (most accurate)
            if isbn:
                clean_isbn = isbn.strip().replace("-", "").replace(" ", "")
                # Only use ISBN-13 (13 digits)
                if len(clean_isbn) == 13:
                    isbn_url = f"{CoverService.BOOKCOVER_API_BASE_URL}/bookcover/{clean_isbn}"
                    logger.info(f"🔍 Calling bookcover-api: {isbn_url}")
                    
                    try:
                        response = requests.get(isbn_url, timeout=10)
                        logger.info(f"📡 bookcover-api response: status={response.status_code}")
                        if response.status_code == 200:
                            data = response.json()
                            cover_url = data.get("url")
                            if cover_url:
                                logger.info(f"📥 Fetching image from: {cover_url[:80]}...")
                                # Fetch the actual image
                                img_response = requests.get(cover_url, timeout=10)
                                if img_response.status_code == 200 and img_response.content:
                                    logger.info(f"✅ Found cover from bookcover-api (ISBN: {clean_isbn})")
                                    return img_response.content
                    except Exception as e:
                        logger.debug(f"ISBN lookup failed on bookcover-api: {e}")
            
            # Strategy 2: Try title and author search
            clean_title = title.strip() if title else ""
            if not clean_title:
                return None
            
            clean_author = author.strip() if author else ""
            
            # Build query parameters
            params = {"book_title": clean_title}
            if clean_author:
                params["author_name"] = clean_author
            
            search_url = f"{CoverService.BOOKCOVER_API_BASE_URL}/bookcover"
            logger.info(f"🔍 Calling bookcover-api: {search_url}?book_title={clean_title}&author_name={clean_author or 'Unknown'}")
            
            response = requests.get(search_url, params=params, timeout=10)
            logger.info(f"📡 bookcover-api response: status={response.status_code}")
            if response.status_code != 200:
                logger.info(f"❌ bookcover-api search failed: status={response.status_code}")
                return None
            
            data = response.json()
            cover_url = data.get("url")
            
            if not cover_url:
                logger.info("❌ bookcover-api returned no URL")
                return None
            
            logger.info(f"📥 Fetching image from: {cover_url[:80]}...")
            # Fetch the actual image from the URL
            img_response = requests.get(cover_url, timeout=10)
            if img_response.status_code == 200 and img_response.content and len(img_response.content) > 0:
                logger.info(f"✅ Found cover from bookcover-api: {clean_title}")
                return img_response.content
            else:
                logger.debug(f"Failed to fetch image from bookcover-api URL: status={img_response.status_code}")
                return None
            
        except Exception as e:
            logger.debug(f"bookcover-api error: {e}")
            return None
    
    @staticmethod
    def fetch_from_open_library(title: str, author: Optional[str] = None) -> Optional[bytes]:
        """
        Fetch cover from Open Library API (free, no API key required)
        Returns image bytes or None if not found
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
            
            logger.info(f"🔍 Calling Open Library: {search_url}?q={query[:50]}...")
            response = requests.get(search_url, params=params, timeout=10)
            logger.info(f"📡 Open Library response: status={response.status_code}")
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
                if isinstance(isbns, list) and len(isbns) > 0:
                    isbn = isbns[0]
                elif isinstance(isbns, str) and isbns:
                    isbn = isbns
            
            # Try cover ID first (most reliable)
            if cover_id:
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                img_response = requests.get(cover_url, timeout=10)
                if img_response.status_code == 200 and img_response.content and len(img_response.content) > 0:
                    logger.info(f"✅ Found cover from Open Library (cover_id: {cover_id})")
                    return img_response.content
                else:
                    logger.debug(f"Open Library cover image request failed: status={img_response.status_code}, content_length={len(img_response.content) if img_response.content else 0}")
            
            # Fallback to ISBN
            if isbn:
                cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
                img_response = requests.get(cover_url, timeout=10)
                if img_response.status_code == 200 and img_response.content and len(img_response.content) > 0:
                    logger.info(f"✅ Found cover from Open Library (ISBN: {isbn})")
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
        Fetch cover from Google Books API (free, no API key required)
        Returns image bytes or None if not found
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
            
            logger.info(f"🔍 Calling Google Books: {search_url}?q={query[:50]}...")
            response = requests.get(search_url, params=params, timeout=10)
            logger.info(f"📡 Google Books response: status={response.status_code}")
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
                        logger.info(f"✅ Found cover from Google Books (size: {size})")
                        return img_response.content
                    else:
                        logger.debug(f"Google Books cover request failed for size {size}: status={img_response.status_code}, content_length={len(img_response.content) if img_response.content else 0}")
            
            return None
            
        except Exception as e:
            logger.error(f"Google Books API error: {e}", exc_info=True)
            return None
    
    def fetch_cover(self, title: str, author: Optional[str] = None, isbn: Optional[str] = None, image_url: Optional[str] = None) -> Optional[Tuple[bytes, str]]:
        """
        Fetch cover with B2 caching, trying multiple sources.
        Returns tuple of (image_bytes, content_type) or None if not found.
        
        Tries in order (priority):
        0. B2 Cache (if available) - instant, no external API calls
        1. bookcover-api (Goodreads) - with ISBN if available
        2. bookcover-api (Goodreads) - with title and author
        3. bookcover-api (Goodreads) - with simplified title
        4. Open Library API (with full title)
        5. Open Library API (with simplified title)
        6. Google Books API (with full title)
        7. Google Books API (with simplified title)
        """
        # Clean title and author
        clean_title = title.strip() if title else ""
        clean_author = author.strip() if author else None
        clean_isbn = isbn.strip() if isbn else None
        clean_image_url = image_url.strip() if image_url else None
        
        if not clean_title:
            logger.warning("No title provided for cover fetch")
            return None
        
        logger.info(f"Fetching cover for: '{clean_title}' by {clean_author or 'Unknown'}" + 
                   (f" (ISBN: {clean_isbn})" if clean_isbn else ""))
        
        # PRIORITY 0: Check B2 cache first (fastest, no external API calls)
        cached_cover = self.get_from_b2_cache(clean_title, clean_author, clean_isbn, clean_image_url)
        if cached_cover:
            return (cached_cover, "image/jpeg")
        
        # PRIORITY 1: Try bookcover-api first (best quality from Goodreads)
        cover_data = CoverService.fetch_from_bookcover_api(clean_title, clean_author, clean_isbn)
        if cover_data:
            # Store to B2 cache for future requests
            self.store_to_b2_cache(cover_data, clean_title, clean_author, clean_isbn, clean_image_url)
            return (cover_data, "image/jpeg")
        
        # Try with simplified title on bookcover-api
        simplified_title = CoverService._simplify_title(clean_title)
        if simplified_title != clean_title:
            logger.info(f"🔄 Trying simplified title on bookcover-api: '{simplified_title}'")
            cover_data = CoverService.fetch_from_bookcover_api(simplified_title, clean_author, clean_isbn)
            if cover_data:
                # Store to B2 cache for future requests
                self.store_to_b2_cache(cover_data, clean_title, clean_author, clean_isbn, clean_image_url)
                return (cover_data, "image/jpeg")
        
        # PRIORITY 2: Fallback to Open Library
        logger.info("⏭️  bookcover-api failed, trying Open Library...")
        cover_data = CoverService.fetch_from_open_library(clean_title, clean_author)
        if cover_data:
            # Store to B2 cache for future requests
            self.store_to_b2_cache(cover_data, clean_title, clean_author, clean_isbn, clean_image_url)
            return (cover_data, "image/jpeg")
        
        # Try with simplified title on Open Library
        if simplified_title != clean_title:
            logger.info(f"🔄 Trying simplified title on Open Library: '{simplified_title}'")
            cover_data = CoverService.fetch_from_open_library(simplified_title, clean_author)
            if cover_data:
                # Store to B2 cache for future requests
                self.store_to_b2_cache(cover_data, clean_title, clean_author, clean_isbn, clean_image_url)
                return (cover_data, "image/jpeg")
        
        # PRIORITY 3: Fallback to Google Books (lowest priority)
        logger.info("⏭️  Open Library failed, trying Google Books...")
        cover_data = CoverService.fetch_from_google_books(clean_title, clean_author)
        if cover_data:
            # Store to B2 cache for future requests
            self.store_to_b2_cache(cover_data, clean_title, clean_author, clean_isbn, clean_image_url)
            return (cover_data, "image/jpeg")
        
        # Try Google Books with simplified title
        if simplified_title != clean_title:
            logger.info(f"🔄 Trying simplified title on Google Books: '{simplified_title}'")
            cover_data = CoverService.fetch_from_google_books(simplified_title, clean_author)
            if cover_data:
                # Store to B2 cache for future requests
                self.store_to_b2_cache(cover_data, clean_title, clean_author, clean_isbn, clean_image_url)
                return (cover_data, "image/jpeg")
        
        logger.warning(f"No cover found for: '{clean_title}' by {clean_author or 'Unknown'}")
        return None
    
    @staticmethod
    def _simplify_title(title: str) -> str:
        """Simplify title by removing special characters, quotes, and extra whitespace"""
        import re
        # Remove common special characters but keep basic punctuation
        simplified = re.sub(r'[^\w\s-]', ' ', title)
        # Collapse multiple spaces
        simplified = re.sub(r'\s+', ' ', simplified)
        return simplified.strip()

# Initialize cover_service without B2 (will be set by endpoints when needed)
cover_service = CoverService()

