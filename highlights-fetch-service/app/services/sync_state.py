"""
Sync state management for background sync operations.
Thread-safe in-memory storage for sync status tracking.
"""
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    UP_TO_DATE = "up_to_date"
    ERROR = "error"


class SyncState:
    """Thread-safe singleton for tracking sync state"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.status: SyncStatus = SyncStatus.IDLE
        self.message: str = ""
        self.progress: Optional[float] = None  # 0-100 for future progress tracking
        self.error: Optional[str] = None
        self.last_sync_time: Optional[datetime] = None
        self.file_size_mb: Optional[float] = None
        self._state_lock = Lock()
        self._initialized = True
        logger.info("SyncState initialized")
    
    def set_checking(self):
        """Set status to checking"""
        with self._state_lock:
            self.status = SyncStatus.CHECKING
            self.message = "Checking for updates..."
            self.error = None
            self.progress = None
            logger.info("Sync status: CHECKING")
    
    def set_downloading(self, file_size_mb: Optional[float] = None):
        """Set status to downloading"""
        with self._state_lock:
            self.status = SyncStatus.DOWNLOADING
            self.message = "Downloading database..."
            self.error = None
            self.progress = 0.0
            self.file_size_mb = file_size_mb
            logger.info(f"Sync status: DOWNLOADING (size: {file_size_mb:.2f} MB)" if file_size_mb else "Sync status: DOWNLOADING")
    
    def set_completed(self, file_size_mb: Optional[float] = None):
        """Set status to completed"""
        with self._state_lock:
            self.status = SyncStatus.COMPLETED
            self.message = f"Sync completed ({file_size_mb:.2f} MB)" if file_size_mb else "Sync completed"
            self.error = None
            self.progress = 100.0
            self.last_sync_time = datetime.now(timezone.utc)
            self.file_size_mb = file_size_mb
            logger.info(f"Sync status: COMPLETED (size: {file_size_mb:.2f} MB)" if file_size_mb else "Sync status: COMPLETED")
    
    def set_up_to_date(self):
        """Set status to up-to-date"""
        with self._state_lock:
            self.status = SyncStatus.UP_TO_DATE
            self.message = "Database is up to date"
            self.error = None
            self.progress = None
            logger.info("Sync status: UP_TO_DATE")
    
    def set_error(self, error_message: str):
        """Set status to error"""
        with self._state_lock:
            self.status = SyncStatus.ERROR
            self.message = "Sync failed"
            self.error = error_message
            self.progress = None
            logger.error(f"Sync status: ERROR - {error_message}")
    
    def set_idle(self):
        """Reset to idle state"""
        with self._state_lock:
            self.status = SyncStatus.IDLE
            self.message = ""
            self.error = None
            self.progress = None
            logger.info("Sync status: IDLE")
    
    def get_state(self) -> dict:
        """Get current state as dict (thread-safe)"""
        with self._state_lock:
            return {
                "status": self.status.value,
                "message": self.message,
                "progress": self.progress,
                "error": self.error,
                "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
                "file_size_mb": self.file_size_mb
            }
    
    def is_busy(self) -> bool:
        """Check if sync is currently in progress"""
        with self._state_lock:
            return self.status in [SyncStatus.CHECKING, SyncStatus.DOWNLOADING]


# Global singleton instance
sync_state = SyncState()

