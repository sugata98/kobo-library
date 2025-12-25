import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    B2_APPLICATION_KEY_ID: str
    B2_APPLICATION_KEY: str
    B2_BUCKET_NAME: str
    LOCAL_DB_PATH: str = "/tmp/KoboReader.sqlite"

    class Config:
        env_file = ".env"

settings = Settings()

