"""
Kobo AI Companion API Endpoints

Provides endpoints for:
1. Receiving questions/highlights from Kobo device
2. Telegram webhook for conversational AI
"""

from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks, Response
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.core.config import settings

# Global variable for companion service (initialized in main.py lifespan)
kobo_companion = None
telegram_app = None

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class KoboContext(BaseModel):
    """Context information from Kobo device"""
    book: str = Field(..., description="Book title")
    author: str = Field(..., description="Author name")
    chapter: Optional[str] = Field(None, description="Chapter name")
    device_id: Optional[str] = Field(None, description="Kobo device identifier")


class KoboAskRequest(BaseModel):
    """Model for Kobo ask/explain request"""
    mode: str = Field(..., description="Mode: 'explain', 'summarize', etc.")
    text: str = Field(..., description="The selected text to explain")
    context: KoboContext = Field(..., description="Reading context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "explain",
                "text": "Load balancers distribute traffic across multiple servers...",
                "context": {
                    "book": "System Design Interview",
                    "author": "Alex Xu",
                    "chapter": "Chapter 2: Scalability",
                    "device_id": "kobo-sarthak"
                }
            }
        }


@router.post("/kobo-ask")
async def kobo_ask(
    request: KoboAskRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """
    Receive a question/highlight from Kobo device and provide immediate explanation.
    
    This endpoint:
    1. Validates the API key
    2. Generates quick explanation with Gemini (returns immediately)
    3. Sends full analysis to Telegram in background (with images)
    
    Args:
        request: The Kobo ask request with text and context
        background_tasks: FastAPI background tasks
        x_api_key: API key from X-API-Key header
        
    Returns:
        Plain text explanation (for Kobo dialog box)
        
    Raises:
        HTTPException: If authentication fails or service is unavailable
    """
    # Validate API key
    if not settings.KOBO_API_KEY:
        logger.error("KOBO_API_KEY not configured")
        raise HTTPException(
            status_code=500,
            detail="API key authentication not configured"
        )
    
    if x_api_key != settings.KOBO_API_KEY.get_secret_value():
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Check if companion is initialized
    if not kobo_companion:
        logger.error("Kobo AI Companion not initialized")
        raise HTTPException(
            status_code=503,
            detail="Kobo AI Companion service is not available. Check TELEGRAM_ENABLED and credentials."
        )
    
    # Process the request
    try:
        logger.info(f"Received {request.mode} request from '{request.context.book}' by {request.context.author}")
        
        # Generate quick explanation (2-3 seconds)
        explanation = await kobo_companion._generate_analysis(
            text=request.text,
            book=request.context.book,
            author=request.context.author,
            chapter=request.context.chapter
        )
        
        # Schedule background task: send full analysis to Telegram (with images)
        background_tasks.add_task(
            kobo_companion.send_highlight_with_analysis,
            text=request.text,
            book=request.context.book,
            author=request.context.author,
            chapter=request.context.chapter
        )
        
        logger.info(f"Returning explanation to Kobo, Telegram update scheduled")
        
        # Return plain text for Kobo dialog (no JSON, no formatting)
        return Response(content=explanation, media_type="text/plain")
            
    except Exception as e:
        logger.error(f"Error processing Kobo request: {e}", exc_info=True)
        # Return error message as plain text (will show in Kobo dialog)
        error_msg = "Sorry, I encountered an error processing your request. Please try again."
        return Response(content=error_msg, media_type="text/plain", status_code=500)


@router.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """
    Webhook endpoint for Telegram updates.
    
    This handles incoming messages from Telegram, specifically:
    - User replies to bot messages (conversation mode)
    
    Args:
        request: FastAPI request object containing Telegram update
        
    Returns:
        Success response
    """
    if not telegram_app:
        logger.warning("Telegram webhook called but app not initialized")
        raise HTTPException(
            status_code=503,
            detail="Telegram service not available"
        )
    
    try:
        # Import here to avoid circular dependency
        from telegram import Update
        
        # Parse the update from Telegram
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        
        # Process the update
        await telegram_app.process_update(update)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}", exc_info=True)
        # Return 200 anyway to prevent Telegram from retrying
        return {"status": "error", "message": str(e)}


@router.get("/telegram-webhook-info")
async def get_webhook_info():
    """
    Get current Telegram webhook configuration.
    
    Useful for debugging webhook setup.
    
    Returns:
        Webhook information from Telegram
    """
    if not telegram_app:
        raise HTTPException(
            status_code=503,
            detail="Telegram service not available"
        )
    
    try:
        webhook_info = await telegram_app.bot.get_webhook_info()
        return {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting webhook info: {str(e)}"
        )

