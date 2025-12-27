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
    
    # Authentication settings
    AUTH_ENABLED: bool = True  # Set to False to disable authentication
    AUTH_USERNAME: str  # Set via environment variable
    AUTH_PASSWORD: str  # Set via environment variable
    JWT_SECRET_KEY: str  # Set via environment variable - use a long random string!
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    class Config:
        env_file = ".env"

settings = Settings()

