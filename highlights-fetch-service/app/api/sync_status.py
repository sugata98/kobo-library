from fastapi import APIRouter, BackgroundTasks, Depends
from app.services.db_sync import db_sync_service
from app.services.sync_state import sync_state, SyncStatus
from app.core.auth import require_auth
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def run_sync_in_background():
    """Background task to run sync with state tracking"""
    try:
        db_sync_service.sync_with_state_tracking()
    except Exception as e:
        logger.error(f"Background sync failed: {e}")
        sync_state.set_error(str(e))


@router.post("/check-and-sync")
async def check_and_sync(
    background_tasks: BackgroundTasks,
    username: str = Depends(require_auth)
):
    """
    Initiate sync check in background and return immediately.
    Client should poll /sync-status for progress.
    """
    try:
        # If already syncing, return current status
        if sync_state.is_busy():
            return {
                "initiated": False,
                "message": "Sync already in progress",
                **sync_state.get_state()
            }
        
        # If recently completed, check if we need to sync again
        current_status = sync_state.status
        if current_status in [SyncStatus.COMPLETED, SyncStatus.UP_TO_DATE]:
            # Check if we need to sync again
            if not db_sync_service.is_local_cache_stale():
                return {
                    "initiated": False,
                    "message": "Database is already up to date",
                    **sync_state.get_state()
                }
        
        # Reset state and start background sync
        sync_state.set_idle()
        background_tasks.add_task(run_sync_in_background)
        
        return {
            "initiated": True,
            "message": "Sync initiated in background",
            "status": "checking"
        }
        
    except Exception as e:
        logger.error(f"Error initiating sync: {e}")
        sync_state.set_error(str(e))
        return {
            "initiated": False,
            "message": f"Failed to initiate sync: {str(e)}",
            "status": "error",
            "error": str(e)
        }


@router.get("/sync-status")
async def get_sync_status(username: str = Depends(require_auth)):
    """
    Get current sync status for polling.
    Returns status, progress, and any error information.
    """
    state = sync_state.get_state()
    
    return {
        **state,
        "is_syncing": sync_state.is_busy(),
        "needs_reload": state["status"] == SyncStatus.COMPLETED.value
    }
