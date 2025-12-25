from b2sdk.v2 import InMemoryAccountInfo, B2Api
from app.core.config import settings
import os
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

class B2Service:
    def __init__(self):
        self.info = InMemoryAccountInfo()
        self.b2_api = B2Api(self.info)
        self.bucket = None
        try:
            self.b2_api.authorize_account("production", settings.B2_APPLICATION_KEY_ID, settings.B2_APPLICATION_KEY)
            self.bucket = self.b2_api.get_bucket_by_name(settings.B2_BUCKET_NAME)
            logger.info("Successfully connected to B2 Cloud")
        except Exception as e:
            logger.warning(f"Failed to connect to B2 Cloud: {e}. Sync features will not work until credentials are configured.")

    def _ensure_connected(self):
        if not self.bucket:
            try:
                self.b2_api.authorize_account("production", settings.B2_APPLICATION_KEY_ID, settings.B2_APPLICATION_KEY)
                self.bucket = self.b2_api.get_bucket_by_name(settings.B2_BUCKET_NAME)
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

b2_service = B2Service()
