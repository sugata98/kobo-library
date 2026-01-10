from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.api.auth import router as auth_router
from app.api.sync_status import router as sync_status_router
from app.api import kobo_companion
from app.services.db_sync import db_sync_service
from app.services.kobo_ai_companion import create_kobo_ai_companion, create_telegram_application
from app.core.config import settings
from contextlib import asynccontextmanager
import asyncio
import os
import logging

logger = logging.getLogger(__name__)


def configure_logging():
    """
    Configure logging for the application in an idempotent way.
    Only sets up logging if it hasn't been configured yet.
    This prevents conflicts when the app is imported or embedded.
    """
    root_logger = logging.getLogger()
    
    # Check if logging is already configured (has handlers)
    if root_logger.handlers:
        logger.info("Logging already configured, skipping setup")
        return
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("Logging configured successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown").
    """
    # Startup: Configure logging and sync database if needed
    configure_logging()
    logger.info("Application starting up...")
    
    # Run blocking I/O operations in thread pool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    
    try:
        # Check if database exists (non-blocking)
        local_mtime = await loop.run_in_executor(None, db_sync_service.get_local_file_mtime)
        
        if local_mtime == 0:
            logger.warning("No local database cache found - initial sync required")
            logger.info("Initiating database download from B2...")
            
            # Run sync in thread pool (non-blocking)
            sync_result = await loop.run_in_executor(None, db_sync_service.sync_if_needed)
            
            if not sync_result:
                # Sync failed - this is critical, we have no database
                error_msg = (
                    "CRITICAL: Initial database sync failed and no local cache exists. "
                    "Server cannot start without a database. "
                    "Please check B2 credentials, network connectivity, and B2 bucket contents."
                )
                logger.error(error_msg)
                logger.error("Aborting startup - server cannot operate without database")
                raise SystemExit(1)
            
            logger.info("Initial database sync completed successfully")
            
            # Verify the database file actually exists after sync
            final_mtime = await loop.run_in_executor(None, db_sync_service.get_local_file_mtime)
            if final_mtime == 0:
                error_msg = (
                    "CRITICAL: Database file not found after successful sync. "
                    "This indicates a file system issue or incorrect LOCAL_DB_PATH configuration."
                )
                logger.error(error_msg)
                raise SystemExit(1)
        else:
            logger.info(f"Local database cache exists (mtime: {local_mtime}), skipping initial sync")
    
    except SystemExit:
        # Re-raise SystemExit to abort startup
        raise
    except Exception as e:
        # Unexpected error during startup
        logger.error(f"Unexpected error during startup sync: {e}", exc_info=True)
        logger.error("Aborting startup due to unexpected error")
        raise SystemExit(1)
    
    logger.info("Application ready - database available")
    
    # Initialize Kobo AI Companion (if enabled)
    if settings.TELEGRAM_ENABLED:
        logger.info("Initializing Kobo AI Companion...")
        kobo_companion.kobo_companion = create_kobo_ai_companion()
        
        if kobo_companion.kobo_companion:
            logger.info("✅ Kobo AI Companion initialized successfully")
        else:
            logger.warning("⚠️  Failed to initialize Kobo AI Companion")
        
        # Initialize Telegram application for webhooks
        kobo_companion.telegram_app = await create_telegram_application()
        if kobo_companion.telegram_app:
            await kobo_companion.telegram_app.initialize()
            logger.info("✅ Telegram application initialized for webhook mode")
            
            # Set webhook if URL is configured (only in one worker to avoid rate limits)
            if settings.TELEGRAM_WEBHOOK_URL:
                webhook_url = f"{settings.TELEGRAM_WEBHOOK_URL}/telegram-webhook"
                
                # Use a lock file to ensure only one worker sets the webhook
                lock_file = "/tmp/.telegram_webhook.lock"
                try:
                    # Try to create lock file atomically
                    import fcntl
                    lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    try:
                        await kobo_companion.telegram_app.bot.set_webhook(url=webhook_url)
                        logger.info(f"✅ Telegram webhook set to: {webhook_url}")
                    finally:
                        os.close(lock_fd)
                except FileExistsError:
                    # Another worker already set the webhook
                    logger.info("ℹ️  Telegram webhook already set by another worker")
                except Exception as e:
                    logger.error(f"❌ Failed to set webhook: {e}")
            else:
                logger.warning("⚠️  TELEGRAM_WEBHOOK_URL not set - webhook not configured")
        else:
            logger.warning("⚠️  Failed to initialize Telegram application")
    else:
        logger.info("ℹ️  Kobo AI Companion is disabled (TELEGRAM_ENABLED=False)")
    
    # Yield control to the application
    yield
    
    # Shutdown: cleanup if needed
    logger.info("Application shutting down...")
    if kobo_companion.telegram_app:
        await kobo_companion.telegram_app.shutdown()
        logger.info("✅ Telegram application shut down")


app = FastAPI(lifespan=lifespan)

# CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "*")
if frontend_url != "*" and "," in frontend_url:
    allowed_origins = [origin.strip() for origin in frontend_url.split(",")]
else:
    allowed_origins = [frontend_url] if frontend_url != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(sync_status_router, prefix="/api", tags=["sync"])
app.include_router(api_router, prefix="/api")
app.include_router(kobo_companion.router, tags=["kobo-ai-companion"])

@app.get("/")
def read_root():
    return {
        "message": "Readr API is running",
        "features": {
            "library": "enabled",
            "ai_companion": settings.TELEGRAM_ENABLED
        }
    }

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    """Health check endpoint for uptime monitoring services.
    Supports both GET and HEAD requests."""
    return {
        "status": "ok",
        "ai_companion": {
            "enabled": settings.TELEGRAM_ENABLED,
            "companion_initialized": kobo_companion.kobo_companion is not None,
            "telegram_initialized": kobo_companion.telegram_app is not None
        }
    }
