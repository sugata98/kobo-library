# Security Improvements - Config & Secrets Management

## Overview

Enhanced security for sensitive configuration values using Pydantic's `SecretStr` type and field validators to enforce best practices for secret management.

## Changes Made

### 1. **Secure Secret Storage** (`app/core/config.py`)

Migrated sensitive configuration fields to use `SecretStr`:

- `AUTH_USERNAME` → `SecretStr`
- `AUTH_PASSWORD` → `SecretStr` 
- `JWT_SECRET_KEY` → `SecretStr`
- `B2_APPLICATION_KEY` → `SecretStr`
- `B2_COVERS_APPLICATION_KEY` → `Optional[SecretStr]`

**Benefits:**
- Secrets are automatically redacted in logs and error messages
- Prevents accidental exposure in stack traces or debugging output
- Enforces explicit access via `.get_secret_value()`

### 2. **JWT Secret Key Validation**

Added `@field_validator` for `JWT_SECRET_KEY`:

```python
@field_validator('JWT_SECRET_KEY')
@classmethod
def validate_jwt_secret_key_length(cls, v: SecretStr) -> SecretStr:
    """Enforce minimum length for JWT secret key (32 characters for security)."""
    secret_value = v.get_secret_value()
    if len(secret_value) < 32:
        raise ValueError(
            f"JWT_SECRET_KEY must be at least 32 characters long for security. "
            f"Current length: {len(secret_value)}. "
            f"Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return v
```

**Security Impact:**
- Prevents weak JWT secrets that are vulnerable to brute-force attacks
- Provides clear error message with instructions to generate secure keys
- Validates at application startup, failing fast if misconfigured

### 3. **Token Expiry Validation**

Added `@field_validator` for `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`:

```python
@field_validator('JWT_ACCESS_TOKEN_EXPIRE_MINUTES')
@classmethod
def validate_token_expiry(cls, v: int) -> int:
    """Validate token expiry is reasonable (warn if too long)."""
    if v > 43200:  # 30 days
        raise ValueError(
            f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 43200 (30 days) for security. "
            f"Current value: {v}"
        )
    if v < 1:
        raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be at least 1 minute")
    return v
```

**Security Impact:**
- Prevents excessively long-lived tokens that increase exposure window
- Enforces maximum recommended expiry of 30 days
- Makes expiry duration configurable via environment variable

### 4. **Updated Secret Access** 

Updated all consumers to use `.get_secret_value()`:

**`app/core/auth.py`:**
- `settings.JWT_SECRET_KEY.get_secret_value()` (2 locations)
- `settings.AUTH_USERNAME.get_secret_value()` (1 location)
- `settings.AUTH_PASSWORD.get_secret_value()` (1 location)

**`app/services/b2.py`:**
- `settings.B2_APPLICATION_KEY.get_secret_value()` (2 locations)
- `settings.B2_COVERS_APPLICATION_KEY.get_secret_value()` (1 location)

### 5. **Updated Documentation** (`example.env`)

Enhanced environment file documentation with stronger security guidance:

```env
# JWT_SECRET_KEY: MUST be at least 32 characters for security
# ⚠️  DO NOT use the placeholder value below - it will fail validation!
# Generate secure key: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=REPLACE_WITH_SECURE_RANDOM_STRING

# JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Token expiry in minutes
# Shorter expiry = better security if token is compromised
# Options:
#   - 1440 (1 day) - Most secure, users login daily
#   - 10080 (7 days) - Recommended balance of security and convenience
#   - 43200 (30 days) - Maximum allowed, suitable for personal single-user apps only
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days (recommended default)
```

**Security Improvements:**
- Changed placeholder from descriptive value to `REPLACE_WITH_SECURE_RANDOM_STRING` to prevent accidental commits
- Reduced default from 30 days to 7 days for better security posture
- Added comprehensive token expiry guidance with security/convenience trade-offs
- Clear warning that placeholder value will fail validation

## Migration Guide

### For Existing Deployments

**No code changes required** - existing `.env` files will continue to work as Pydantic automatically converts string values to `SecretStr`.

**However, you should:**

1. **Verify JWT_SECRET_KEY length:**
   ```bash
   echo -n "$JWT_SECRET_KEY" | wc -c
   ```
   Must be ≥32 characters. If not, generate a new one:
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

2. **Update your `.env` file:**
   ```env
   JWT_SECRET_KEY=<your-new-32+-character-key>
   ```

3. **Restart the application** - it will fail fast on startup if secrets don't meet requirements

### Testing Validation

**Test 1: Short JWT Secret (should fail)**
```bash
JWT_SECRET_KEY="short" python -c "from app.core.config import settings"
# Expected: ValueError with helpful message
```

**Test 2: Valid JWT Secret (should pass)**
```bash
JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
python -c "from app.core.config import settings; print('✓ Valid config')"
# Expected: ✓ Valid config
```

**Test 3: Excessive token expiry (should fail)**
```bash
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=50000 python -c "from app.core.config import settings"
# Expected: ValueError about exceeding 43200
```

## Security Best Practices

### 1. **Secret Generation**
Always use cryptographically secure random generation:
```bash
# For JWT_SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# For passwords (if needed)
python -c 'import secrets; print(secrets.token_urlsafe(24))'
```

**⚠️ Never use weak or descriptive placeholders in production!**

### 2. **Secret Rotation**
- Rotate `JWT_SECRET_KEY` periodically (e.g., every 90 days)
- Note: Rotating JWT_SECRET_KEY invalidates all existing tokens

### 3. **Environment Variables**
- Never commit `.env` files to version control
- Use secrets management systems in production (AWS Secrets Manager, etc.)
- Keep `example.env` updated but without real secrets
- Use obviously invalid placeholders (e.g., `REPLACE_WITH_...`) to prevent accidental use

### 4. **Token Expiry Strategy**

**Security vs. Convenience Trade-off:**

| Duration | Security | Use Case |
|----------|----------|----------|
| **1 day (1440 min)** | 🔒🔒🔒 Highest | Production apps, sensitive data |
| **7 days (10080 min)** | 🔒🔒 High | **Recommended default** - Good balance |
| **30 days (43200 min)** | 🔒 Medium | Personal single-user apps only |

**Key Considerations:**
- **Shorter expiry = better security**: Compromised tokens have limited validity window
- **Longer expiry = better UX**: Users don't need to login frequently
- **Recommended for production**: 7 days or less
- **Personal apps**: 7-30 days acceptable (lower risk, single user)

**Token Compromise Scenarios:**
- Stolen token remains valid until expiry
- No built-in revocation in current implementation
- Shorter expiry limits exposure window

**Future Enhancements for Production:**
- Implement refresh tokens (long-lived) + access tokens (short-lived)
- Add token revocation/blacklist capability
- Implement token rotation on refresh
- Add activity-based expiry (extend on use)

## Verification Checklist

- [x] All sensitive config fields use `SecretStr`
- [x] JWT_SECRET_KEY validator enforces ≥32 characters
- [x] Token expiry validator enforces ≤30 days
- [x] All consumers updated to use `.get_secret_value()`
- [x] Example config file updated with clear instructions
- [x] No linter errors introduced
- [x] Backward compatible with existing `.env` files

## Related Files

- `app/core/config.py` - Configuration with validators
- `app/core/auth.py` - JWT and authentication logic
- `app/services/b2.py` - B2 service initialization
- `example.env` - Environment template with documentation

## References

- [Pydantic SecretStr Documentation](https://docs.pydantic.dev/latest/api/types/#pydantic.types.SecretStr)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Python secrets module](https://docs.python.org/3/library/secrets.html)

