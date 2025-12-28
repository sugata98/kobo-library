import os
import logging
from datetime import datetime, timezone
from app.services.b2 import b2_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseSyncService:
    def __init__(self):
        self.local_path = settings.LOCAL_DB_PATH
        self.b2_path = "kobo/KoboReader.sqlite"
    
    def get_local_file_mtime(self) -> float:
        """Get local file modification time"""
        if not os.path.exists(self.local_path):
            return 0
        return os.path.getmtime(self.local_path)
    
    def get_b2_file_mtime(self) -> float:
        """Get B2 file modification time"""
        try:
            file_info = b2_service.get_file_info(self.b2_path)
            if file_info:
                return file_info['upload_timestamp'] / 1000.0
            return 0
        except Exception as e:
            logger.error(f"Error getting B2 file info: {e}")
            return 0
    
    def is_local_cache_stale(self) -> bool:
        """Check if B2 has newer version than local cache"""
        local_mtime = self.get_local_file_mtime()
        b2_mtime = self.get_b2_file_mtime()
        
        # Always log timestamps for debugging
        local_time_str = datetime.fromtimestamp(local_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if local_mtime > 0 else "N/A"
        b2_time_str = datetime.fromtimestamp(b2_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if b2_mtime > 0 else "N/A"
        logger.info(f"Timestamp check - Local: {local_time_str} ({local_mtime}), B2: {b2_time_str} ({b2_mtime})")
        
        if local_mtime == 0:
            logger.info("No local file found")
            return True
        
        if b2_mtime == 0:
            logger.warning("Could not get B2 timestamp")
            return False
        
        is_stale = b2_mtime > (local_mtime + 1)
        logger.info(f"Is stale? {is_stale} (B2 > Local+1s: {b2_mtime} > {local_mtime + 1})")
        
        return is_stale
    
    def sync_if_needed(self) -> bool:
        """Download from B2 if needed"""
        try:
            if self.is_local_cache_stale():
                logger.info("Syncing from B2...")
                
                # Get B2 timestamp before download
                b2_mtime = self.get_b2_file_mtime()
                
                if os.path.exists(self.local_path):
                    os.remove(self.local_path)
                
                os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
                b2_service.download_file(self.b2_path, self.local_path)
                
                if os.path.exists(self.local_path):
                    # Set local file's mtime to match B2 to prevent re-downloads
                    if b2_mtime > 0:
                        os.utime(self.local_path, (b2_mtime, b2_mtime))
                        logger.info(f"Set local mtime to match B2: {datetime.fromtimestamp(b2_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    size_mb = os.path.getsize(self.local_path) / (1024 * 1024)
                    logger.info(f"Synced ({size_mb:.2f} MB)")
                    return True
                return False
            return False
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False

db_sync_service = DatabaseSyncService()
