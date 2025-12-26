from b2sdk.v2 import InMemoryAccountInfo, B2Api
from app.core.config import settings
import os
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

class B2Service:
    def __init__(self, key_id=None, app_key=None, bucket_name=None, service_name="B2"):
        """
        Initialize B2 service with optional custom credentials.
        If credentials not provided, uses default from settings.
        """
        self.service_name = service_name
        self.key_id = key_id or settings.B2_APPLICATION_KEY_ID
        self.app_key = app_key or settings.B2_APPLICATION_KEY
        self.bucket_name = bucket_name or settings.B2_BUCKET_NAME
        
        self.info = InMemoryAccountInfo()
        self.b2_api = B2Api(self.info)
        self.bucket = None
        try:
            self.b2_api.authorize_account("production", self.key_id, self.app_key)
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            logger.info(f"Successfully connected to {service_name} bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Failed to connect to {service_name} bucket '{self.bucket_name}': {e}")

    def _ensure_connected(self):
        if not self.bucket:
            try:
                self.b2_api.authorize_account("production", self.key_id, self.app_key)
                self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            except Exception as e:
                raise Exception(f"B2 Connection failed: {e}")

    def download_file(self, file_name: str, local_path: str):
        self._ensure_connected()
        download_dest = self.bucket.download_file_by_name(file_name)
        download_dest.save_to(local_path, 'wb')
        return local_path

    def list_files(self, prefix: str = ""):
        self._ensure_connected()
        return self.bucket.ls(folder_to_list=prefix)

    def get_file_content(self, file_name: str) -> bytes:
        self._ensure_connected()
        # Download to memory
        # b2sdk download_file_by_name returns a DownloadVersion object
        # we can use save(file_like_object)
        download_dest = self.bucket.download_file_by_name(file_name)
        buffer = BytesIO()
        download_dest.save(buffer)
        buffer.seek(0)
        return buffer.read()
    
    def upload_file(self, file_data: BytesIO, file_name: str, content_type: str = "application/octet-stream"):
        """Upload file to B2 bucket"""
        self._ensure_connected()
        # Upload from BytesIO stream
        file_data.seek(0)  # Ensure we're at the start
        self.bucket.upload_bytes(
            data_bytes=file_data.read(),
            file_name=file_name,
            content_type=content_type
        )
        logger.info(f"Uploaded file to B2: {file_name}")
    
    def get_file_stream(self, file_name: str):
        """
        Get file as a true streaming response generator.
        Uses range requests to download and yield chunks incrementally
        without buffering the entire file in memory.
        """
        self._ensure_connected()
        
        # First, get file info to determine size
        try:
            file_info = self.bucket.get_file_info_by_name(file_name)
            file_size = file_info.size
        except Exception as e:
            logger.error(f"Error getting file info for {file_name}: {e}")
            raise
        
        # Download in chunks using range requests
        chunk_size = 64 * 1024  # 64KB chunks - good balance between performance and memory
        offset = 0
        
        while offset < file_size:
            # Calculate range for this chunk
            end = min(offset + chunk_size - 1, file_size - 1)
            range_header = (offset, end)
            
            try:
                # Download this chunk using range request
                download_dest = self.bucket.download_file_by_name(
                    file_name,
                    range_=range_header
                )
                
                # Read chunk into small buffer and yield immediately
                chunk_buffer = BytesIO()
                download_dest.save(chunk_buffer)
                chunk_buffer.seek(0)
                chunk_data = chunk_buffer.read()
                
                # Yield the chunk immediately (not buffering entire file)
                yield chunk_data
                
                # Move to next chunk
                offset = end + 1
                
            except Exception as e:
                logger.error(f"Error downloading chunk at offset {offset}: {e}")
                raise

# Main B2 service for KoboSync bucket (database and markups)
b2_service = B2Service(
    key_id=settings.B2_APPLICATION_KEY_ID,
    app_key=settings.B2_APPLICATION_KEY,
    bucket_name=settings.B2_BUCKET_NAME,
    service_name="KoboSync"
)

# Separate B2 service for covers bucket (if configured)
# Falls back to main bucket if covers-specific credentials not provided
b2_covers_service = B2Service(
    key_id=settings.B2_COVERS_APPLICATION_KEY_ID or settings.B2_APPLICATION_KEY_ID,
    app_key=settings.B2_COVERS_APPLICATION_KEY or settings.B2_APPLICATION_KEY,
    bucket_name=settings.B2_COVERS_BUCKET_NAME or settings.B2_BUCKET_NAME,
    service_name="Covers Cache"
)
