import os
from pydantic_settings import BaseSettings
from pydantic import SecretStr, field_validator, model_validator, ValidationError
from typing import Optional, Any

class Settings(BaseSettings):
    # B2 credentials for KoboSync bucket (read-only for database syncing)
    B2_APPLICATION_KEY_ID: str
    B2_APPLICATION_KEY: SecretStr
    B2_BUCKET_NAME: str
    
    # B2 credentials for covers bucket (read-write for cover caching)
    # Optional - if not set, will use main bucket credentials
    B2_COVERS_APPLICATION_KEY_ID: Optional[str] = None
    B2_COVERS_APPLICATION_KEY: Optional[SecretStr] = None
    B2_COVERS_BUCKET_NAME: Optional[str] = None
    
    LOCAL_DB_PATH: str = "/tmp/KoboReader.sqlite"
    
    # Authentication settings
    AUTH_ENABLED: bool = True  # Set to False to disable authentication
    AUTH_USERNAME: SecretStr  # Set via environment variable
    AUTH_PASSWORD: SecretStr  # Set via environment variable
    JWT_SECRET_KEY: SecretStr  # Set via environment variable - use a long random string (min 32 chars)!
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days (recommended default), configurable via env, max: 43200 (30 days)
    
    # Cookie settings
    COOKIE_SECURE: bool = False  # Set to True for production (HTTPS)
    COOKIE_SAMESITE: str = "lax"  # Options: "lax", "none", "strict"
    COOKIE_DOMAIN: Optional[str] = None  # Set to parent domain (e.g., ".readr.space") to share across subdomains
    
    # Kobo AI Companion settings
    KOBO_API_KEY: Optional[SecretStr] = None  # API key for Kobo device authentication
    TELEGRAM_BOT_TOKEN: Optional[SecretStr] = None  # Telegram bot API token from @BotFather
    TELEGRAM_CHAT_ID: Optional[str] = None  # Telegram group/chat ID where highlights are sent
    TELEGRAM_WEBHOOK_URL: Optional[str] = None  # Public webhook URL for Telegram (e.g., https://your-app.onrender.com)
    TELEGRAM_ENABLED: bool = False  # Set to True to enable Kobo AI Companion
    
    # Google Gemini AI settings
    GEMINI_API_KEY: Optional[SecretStr] = None  # Google AI Studio API key
    GEMINI_MODEL: str = "gemini-3-flash-preview"  # Model for text analysis (fast, powerful)
    GEMINI_IMAGE_MODEL: Optional[str] = "gemini-2.5-flash-image"  # Model for image generation (set to empty string or None to disable)
    
    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def validate_jwt_secret_key_length(cls, v: SecretStr) -> SecretStr:
        """Enforce minimum length for JWT secret key (32 characters for security)."""
        secret_value = v.get_secret_value()
        if len(secret_value) < 32:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least 32 characters long for security. "
                f"Current length: {len(secret_value)}. "
                f"Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v
    
    @field_validator('JWT_ACCESS_TOKEN_EXPIRE_MINUTES')
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        """Validate token expiry is reasonable (warn if too long)."""
        if v > 43200:  # 30 days
            raise ValueError(
                f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 43200 (30 days) for security. "
                f"Current value: {v}"
            )
        if v < 1:
            raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be at least 1 minute")
        return v
    
    @model_validator(mode='after')
    def validate_telegram_config(self) -> 'Settings':
        """
        Validate Kobo AI Companion configuration when TELEGRAM_ENABLED is True.
        
        Ensures all required fields are set when the feature is enabled.
        """
        if self.TELEGRAM_ENABLED:
            missing_fields = []
            
            # Check required fields
            if not self.KOBO_API_KEY:
                missing_fields.append('KOBO_API_KEY')
            
            if not self.TELEGRAM_BOT_TOKEN:
                missing_fields.append('TELEGRAM_BOT_TOKEN')
            
            if not self.TELEGRAM_CHAT_ID:
                missing_fields.append('TELEGRAM_CHAT_ID')
            
            if not self.TELEGRAM_WEBHOOK_URL:
                missing_fields.append('TELEGRAM_WEBHOOK_URL')
            
            if not self.GEMINI_API_KEY:
                missing_fields.append('GEMINI_API_KEY')
            
            if missing_fields:
                raise ValueError(
                    f"TELEGRAM_ENABLED is True but the following required fields are missing or empty: "
                    f"{', '.join(missing_fields)}. "
                    f"Please set these environment variables or disable the feature by setting TELEGRAM_ENABLED=false."
                )
        
        return self

    class Config:
        env_file = ".env"

settings = Settings()

