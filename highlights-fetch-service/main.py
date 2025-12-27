from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
import os

app = FastAPI()

# Allow CORS for frontend
# Set FRONTEND_URL in environment variables (supports comma-separated list)
# Example: "https://readr.space,https://www.readr.space,https://readr.vercel.app"
frontend_url = os.getenv("FRONTEND_URL", "*")

# Parse multiple origins if comma-separated
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

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Readr API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
