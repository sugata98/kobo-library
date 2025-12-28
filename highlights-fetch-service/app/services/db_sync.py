import os
import logging
import tempfile
import shutil
from datetime import datetime, timezone
from app.services.b2 import b2_service
from app.core.config import settings
from app.services.sync_state import sync_state, SyncStatus

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
        """
        Download from B2 if needed (legacy synchronous method for backward compatibility).
        Uses atomic file operations to prevent data loss on failure.
        """
        temp_file = None
        try:
            if self.is_local_cache_stale():
                logger.info("Syncing from B2...")
                
                # Get B2 timestamp before download
                b2_mtime = self.get_b2_file_mtime()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
                
                # Create temporary file in the same directory for atomic rename
                # (rename only works atomically within the same filesystem)
                temp_fd, temp_file = tempfile.mkstemp(
                    dir=os.path.dirname(self.local_path),
                    prefix='.tmp_kobo_',
                    suffix='.sqlite'
                )
                os.close(temp_fd)  # Close the file descriptor, we'll use the path
                
                try:
                    # Download to temporary file
                    logger.info(f"Downloading to temporary file: {temp_file}")
                    b2_service.download_file(self.b2_path, temp_file)
                    
                    # Verify download succeeded
                    if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                        raise Exception("Downloaded file is missing or empty")
                    
                    # Set mtime on temp file before moving
                    if b2_mtime > 0:
                        os.utime(temp_file, (b2_mtime, b2_mtime))
                        logger.info(f"Set temp file mtime to match B2: {datetime.fromtimestamp(b2_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    size_mb = os.path.getsize(temp_file) / (1024 * 1024)
                    
                    # Atomic rename: replaces old file only after successful download
                    # On POSIX systems, this is atomic even if target exists
                    logger.info(f"Atomically replacing old database with new version ({size_mb:.2f} MB)")
                    shutil.move(temp_file, self.local_path)
                    temp_file = None  # Successfully moved, no cleanup needed
                    
                    logger.info(f"Sync completed successfully ({size_mb:.2f} MB)")
                    return True
                    
                except Exception as e:
                    # Download or move failed, temp file will be cleaned up below
                    logger.error(f"Download failed: {e}")
                    raise
                    
            return False
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False
            
        finally:
            # Clean up temp file if it still exists (download failed)
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file {temp_file}: {cleanup_error}")
    
    def sync_with_state_tracking(self) -> bool:
        """
        Download from B2 if needed with state tracking for background tasks.
        Updates sync_state throughout the process.
        Uses atomic file operations to prevent data loss on failure.
        Returns True if sync was performed, False if already up-to-date.
        """
        temp_file = None
        try:
            # Check if already syncing
            if sync_state.is_busy():
                logger.warning("Sync already in progress, skipping")
                return False
            
            sync_state.set_checking()
            
            if self.is_local_cache_stale():
                logger.info("Database needs sync, starting download...")
                
                # Get B2 file info before download
                b2_mtime = self.get_b2_file_mtime()
                file_info = b2_service.get_file_info(self.b2_path)
                file_size_mb = file_info.get('size', 0) / (1024 * 1024) if file_info else None
                
                sync_state.set_downloading(file_size_mb)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
                
                # Create temporary file in the same directory for atomic rename
                # (rename only works atomically within the same filesystem)
                temp_fd, temp_file = tempfile.mkstemp(
                    dir=os.path.dirname(self.local_path),
                    prefix='.tmp_kobo_',
                    suffix='.sqlite'
                )
                os.close(temp_fd)  # Close the file descriptor, we'll use the path
                
                try:
                    # Download to temporary file
                    logger.info(f"Downloading to temporary file: {temp_file}")
                    b2_service.download_file(self.b2_path, temp_file)
                    
                    # Verify download succeeded
                    if not os.path.exists(temp_file):
                        raise Exception("Downloaded file not found")
                    
                    downloaded_size = os.path.getsize(temp_file)
                    if downloaded_size == 0:
                        raise Exception("Downloaded file is empty")
                    
                    # Set mtime on temp file before moving
                    if b2_mtime > 0:
                        os.utime(temp_file, (b2_mtime, b2_mtime))
                        logger.info(f"Set temp file mtime to match B2: {datetime.fromtimestamp(b2_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    actual_size_mb = downloaded_size / (1024 * 1024)
                    
                    # Atomic rename: replaces old file only after successful download
                    # On POSIX systems, this is atomic even if target exists
                    logger.info(f"Atomically replacing old database with new version ({actual_size_mb:.2f} MB)")
                    shutil.move(temp_file, self.local_path)
                    temp_file = None  # Successfully moved, no cleanup needed
                    
                    sync_state.set_completed(actual_size_mb)
                    logger.info(f"Sync completed successfully ({actual_size_mb:.2f} MB)")
                    return True
                    
                except Exception as e:
                    # Download or move failed, temp file will be cleaned up in finally block
                    error_msg = f"Download failed: {str(e)}"
                    logger.error(error_msg)
                    sync_state.set_error(error_msg)
                    return False
                    
            else:
                logger.info("Database is already up to date")
                sync_state.set_up_to_date()
                return False
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sync failed: {error_msg}")
            sync_state.set_error(error_msg)
            return False
            
        finally:
            # Clean up temp file if it still exists (download failed or exception occurred)
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file {temp_file}: {cleanup_error}")

db_sync_service = DatabaseSyncService()
