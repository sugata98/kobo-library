from app.core.config import settings
print("=== B2 Configuration ===")
print(f"Main bucket: {settings.B2_BUCKET_NAME}")
print(f"Covers bucket: {settings.B2_COVERS_BUCKET_NAME if settings.B2_COVERS_BUCKET_NAME else 'Not set (will use main bucket)'}")
print(f"Covers key ID: {settings.B2_COVERS_APPLICATION_KEY_ID[:20] if settings.B2_COVERS_APPLICATION_KEY_ID else 'Not set'}...")
