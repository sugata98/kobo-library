from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for Authorization header
security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY.get_secret_value(), algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password."""
    # For single-user mode, compare against environment variables
    if username != settings.AUTH_USERNAME.get_secret_value():
        return False
    
    # Simple password comparison for personal use
    # This is acceptable for a single-user personal app
    # For multi-user production, you'd hash passwords and use verify_password()
    return password == settings.AUTH_PASSWORD.get_secret_value()

def get_current_user_from_cookie(request: Request) -> Optional[str]:
    """Extract and validate user from cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    username: str = payload.get("sub")
    if username is None:
        return None
    
    return username

def get_current_user_from_header(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Extract and validate user from Authorization header."""
    if not credentials:
        return None
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    
    username: str = payload.get("sub")
    return username

async def require_auth(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Dependency to require authentication.
    Checks both cookies (for browser) and Authorization header (for API clients).
    """
    # If auth is disabled, allow all requests
    if not settings.AUTH_ENABLED:
        return None
    
    # Try cookie first (browser)
    user = get_current_user_from_cookie(request)
    
    # Try Authorization header (API clients)
    if not user:
        user = get_current_user_from_header(credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

