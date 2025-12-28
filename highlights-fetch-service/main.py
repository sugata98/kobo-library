from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.api.auth import router as auth_router
from app.api.sync_status import router as sync_status_router
from app.services.db_sync import db_sync_service
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

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

# Startup: download DB if cache doesn't exist (fallback)
@app.on_event("startup")
async def startup_event():
    if db_sync_service.get_local_file_mtime() == 0:
        logger.info("No cache, downloading...")
        db_sync_service.sync_if_needed()
    logger.info("Ready")

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(sync_status_router, prefix="/api", tags=["sync"])
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Readr API is running"}

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    """Health check endpoint for uptime monitoring services.
    Supports both GET and HEAD requests."""
    return {"status": "ok"}
