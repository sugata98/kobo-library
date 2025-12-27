from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.auth import authenticate_user, create_access_token, require_auth, get_current_user_from_cookie
from app.core.config import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class VerifyResponse(BaseModel):
    authenticated: bool
    username: Optional[str] = None

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, response: Response):
    """
    Authenticate user and return JWT token.
    Sets httpOnly cookie for browser sessions.
    """
    if not authenticate_user(login_data.username, login_data.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": login_data.username},
        expires_delta=access_token_expires
    )
    
    # Set httpOnly cookie for browser
    # For subdomains (www.readr.space + api.readr.space), set domain to parent domain
    # This allows the cookie to be shared across all *.readr.space subdomains
    cookie_kwargs = {
        "key": "access_token",
        "value": access_token,
        "httponly": True,
        "max_age": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "expires": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "samesite": settings.COOKIE_SAMESITE,
        "secure": settings.COOKIE_SECURE,
    }
    
    # Only set domain if configured (for subdomain sharing)
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN
    
    response.set_cookie(**cookie_kwargs)
    
    logger.info(f"User {login_data.username} logged in successfully")
    
    return LoginResponse(
        access_token=access_token,
        username=login_data.username
    )

@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing the authentication cookie.
    """
    response.delete_cookie(key="access_token")
    logger.info("User logged out")
    return {"message": "Logged out successfully"}

@router.get("/verify", response_model=VerifyResponse)
async def verify(request: Request):
    """
    Verify if the current session is authenticated.
    Returns authentication status without requiring auth (for checking login state).
    """
    # If auth is disabled, always return authenticated
    if not settings.AUTH_ENABLED:
        return VerifyResponse(authenticated=True, username="guest")
    
    user = get_current_user_from_cookie(request)
    
    if user:
        return VerifyResponse(authenticated=True, username=user)
    else:
        return VerifyResponse(authenticated=False)

@router.get("/me")
async def get_current_user(username: str = Depends(require_auth)):
    """
    Get current authenticated user info.
    Requires authentication.
    """
    return {"username": username}

