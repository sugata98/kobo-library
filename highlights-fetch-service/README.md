# Highlights Fetch Service

This directory contains the FastAPI backend service for syncing with B2 Cloud and parsing KoboReader.sqlite.

## Book Cover Service

The service fetches book covers from multiple free APIs with the following priority:

1. **bookcover-api** (Primary) - https://bookcover.longitood.com

   - Fetches high-quality covers from Goodreads
   - Supports both ISBN-13 lookup and title/author search
   - Best quality and most reliable source

2. **Open Library API** (Fallback)

   - Free, no API key required
   - Good coverage for many books

3. **Google Books API** (Fallback)
   - Free, no API key required
   - Wide coverage as final fallback

The cover endpoint (`/books/{book_id}/cover`) accepts optional query parameters:

- `title` - Book title (required if not in database)
- `author` - Book author (optional, improves accuracy)
- `isbn` - ISBN-13 (optional, most accurate for bookcover-api)

Example:

```
GET /api/books/{book_id}/cover?title=Clean+Code&author=Robert+Martin&isbn=9780132350884
```

## Security & Authentication

This service includes JWT-based authentication for secure access. All sensitive configuration values use Pydantic's `SecretStr` for protection.

### Required Security Configuration

**⚠️ CRITICAL: Generate a secure JWT secret** (minimum 32 characters):

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

**Environment Variables:**

- `AUTH_ENABLED` - Enable/disable authentication (default: `true`)
- `AUTH_USERNAME` - Username for login
- `AUTH_PASSWORD` - Password for login
- `JWT_SECRET_KEY` - **REQUIRED**: Must be ≥32 characters (see command above)
- `JWT_ALGORITHM` - JWT signing algorithm (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiry in minutes:
  - Default: `10080` (7 days) - Recommended balance of security and convenience
  - Range: `1` to `43200` (30 days max)
  - **Security Note**: Shorter expiry reduces risk if token is compromised

### Security Features

- ✅ **SecretStr Protection**: All secrets automatically redacted in logs
- ✅ **JWT Secret Validation**: Enforces minimum 32-character length
- ✅ **Token Expiry Limits**: Maximum 30-day token lifetime
- ✅ **Fail-Fast Validation**: Application won't start with weak secrets

See `SECURITY_IMPROVEMENTS.md` for detailed security documentation.

### Test Security Configuration

Run validation tests before deployment:

```bash
python test_config_validation.py
```

## Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set Root Directory to: `highlights-fetch-service`
4. Use the following settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `B2_APPLICATION_KEY_ID`
   - `B2_APPLICATION_KEY`
   - `B2_BUCKET_NAME`
   - `AUTH_USERNAME` - Your login username
   - `AUTH_PASSWORD` - Your login password
   - `JWT_SECRET_KEY` - Generate with: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`
   - `LOCAL_DB_PATH` (optional, defaults to `/tmp/KoboReader.sqlite`)

## Local Development

```bash
# Copy and configure environment variables
cp example.env .env
# Edit .env and set your credentials (especially JWT_SECRET_KEY!)

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Dependency Management

Authentication and security packages are pinned to specific tested versions for security and reproducibility. See `DEPENDENCY_MANAGEMENT.md` for:

- Rationale for pinned versions
- Compatibility notes (especially bcrypt/passlib)
- Update strategy
- Production recommendations (pip-tools, Poetry, hash pinning)
- Security scanning with pip-audit

**Quick check**: Verify pinned versions on PyPI:

```bash
python -m pip index versions python-jose
python -m pip index versions passlib
python -m pip index versions bcrypt
```
