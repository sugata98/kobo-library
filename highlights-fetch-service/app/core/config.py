import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # B2 credentials for KoboSync bucket (read-only for database syncing)
    B2_APPLICATION_KEY_ID: str
    B2_APPLICATION_KEY: str
    B2_BUCKET_NAME: str
    
    # B2 credentials for covers bucket (read-write for cover caching)
    # Optional - if not set, will use main bucket credentials
    B2_COVERS_APPLICATION_KEY_ID: Optional[str] = None
    B2_COVERS_APPLICATION_KEY: Optional[str] = None
    B2_COVERS_BUCKET_NAME: Optional[str] = None
    
    LOCAL_DB_PATH: str = "/tmp/KoboReader.sqlite"

    class Config:
        env_file = ".env"

settings = Settings()

