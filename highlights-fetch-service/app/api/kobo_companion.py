"""
Kobo AI Companion API Endpoints

Provides endpoints for:
1. Receiving highlights from Kobo device
2. Telegram webhook for conversational AI
"""

from fastapi import APIRouter, HTTPException, Header, Request
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
class KoboHighlight(BaseModel):
    """Model for Kobo highlight payload"""
    text: str = Field(..., description="The highlighted text")
    book: str = Field(..., description="Book title")
    author: str = Field(..., description="Author name")
    chapter: Optional[str] = Field(None, description="Chapter name (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Load balancers distribute traffic across multiple servers...",
                "book": "System Design Interview",
                "author": "Alex Xu",
                "chapter": "Chapter 2: Scalability"
            }
        }


class HighlightResponse(BaseModel):
    """Response model for highlight submission"""
    status: str
    message: str
    telegram_message_id: Optional[int] = None


@router.post("/kobo-highlight", response_model=HighlightResponse)
async def receive_kobo_highlight(
    highlight: KoboHighlight,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """
    Receive a highlight from Kobo device and process it.
    
    This endpoint:
    1. Validates the API key
    2. Sends highlight to Telegram
    3. Generates AI analysis
    4. Replies with analysis in Telegram thread
    
    Args:
        highlight: The Kobo highlight data
        x_api_key: API key from X-API-Key header
        
    Returns:
        Response with status and Telegram message ID
        
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
    
    # Process the highlight
    try:
        logger.info(f"Received highlight from '{highlight.book}' by {highlight.author}")
        
        # Send highlight with AI analysis to Telegram
        message_id = await kobo_companion.send_highlight_with_analysis(
            text=highlight.text,
            book=highlight.book,
            author=highlight.author,
            chapter=highlight.chapter
        )
        
        if message_id:
            logger.info(f"Successfully processed highlight, message ID: {message_id}")
            return HighlightResponse(
                status="success",
                message="Highlight sent to Telegram with AI analysis",
                telegram_message_id=message_id
            )
        else:
            logger.error("Failed to send highlight to Telegram")
            raise HTTPException(
                status_code=500,
                detail="Failed to send highlight to Telegram"
            )
            
    except Exception as e:
        logger.error(f"Error processing highlight: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing highlight: {str(e)}"
        )


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

