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
        """
        Return the contents of a file from the configured B2 bucket as bytes.
        
        Downloads the specified file into memory and returns its raw byte content. Ensures the service is connected before attempting the download.
        
        Parameters:
            file_name (str): Path or name of the file in the bucket.
        
        Returns:
            bytes: Full contents of the file.
        """
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
        Provide a generator that yields the file's contents from the bucket in fixed-size binary chunks.
        
        Parameters:
            file_name (str): The name (path) of the file in the bucket to stream.
        
        Returns:
            generator: Yields successive bytes objects containing up to 8192 bytes of file data.
        """
        self._ensure_connected()
        download_dest = self.bucket.download_file_by_name(file_name)
        # Return a generator that yields chunks
        chunk_size = 8192  # 8KB chunks
        buffer = BytesIO()
        download_dest.save(buffer)
        buffer.seek(0)
        
        while True:
            chunk = buffer.read(chunk_size)
            if not chunk:
                break
            yield chunk

b2_service = B2Service()