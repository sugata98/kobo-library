from fastapi import APIRouter, Depends
from app.services.db_sync import db_sync_service
from app.core.auth import require_auth
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/check-and-sync")
def check_and_sync(username: str = Depends(require_auth)):
    """Check if sync is needed and perform it (blocking)."""
    try:
        # sync_if_needed() already checks if sync is needed
        synced = db_sync_service.sync_if_needed()
        
        if synced:
            return {
                "sync_needed": True,
                "sync_status": "completed",
                "message": "Synced"
            }
        else:
            return {
                "sync_needed": False,
                "sync_status": "up_to_date",
                "message": "Up-to-date"
            }
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return {
            "sync_needed": False,
            "sync_status": "error",
            "message": str(e)
        }
