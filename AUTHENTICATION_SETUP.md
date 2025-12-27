# Authentication Setup Guide

## Overview

Readr now includes authentication to protect your personal reading data (highlights, annotations, markups) from public access. This guide explains how to configure and deploy the authentication system.

## 🔒 What's Protected

With authentication enabled, the following endpoints require login:

- **`/api/books`** - Your book and article list
- **`/api/books/{id}`** - Book details
- **`/api/books/{id}/highlights`** - Your highlights (personal annotations)
- **`/api/books/{id}/markups`** - Your handwritten notes and scribbles
- **`/api/sync`** - Database synchronization
- **`/api/markup/{id}/*`** - Markup images (SVG/JPG)

**Book covers (`/api/books/{id}/cover`)** remain accessible as they contain no personal data.

---

## 🚀 Quick Start

### 1. Backend Configuration

Add these environment variables to your backend deployment:

```bash
# Enable authentication
AUTH_ENABLED=true

# Set your credentials (CHANGE THESE!)
AUTH_USERNAME=your-username
AUTH_PASSWORD=your-secure-password

# JWT secret key (IMPORTANT: Use a long random string!)
JWT_SECRET_KEY=your-very-long-random-secret-key-change-this

# Token expiration (default: 30 days)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

### 2. Generate a Secure JWT Secret

Use one of these methods to generate a secure secret key:

```bash
# Method 1: Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Using OpenSSL
openssl rand -base64 32

# Method 3: Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

Copy the output and use it as your `JWT_SECRET_KEY`.

### 3. Install Backend Dependencies

```bash
cd highlights-fetch-service
pip install -r requirements.txt
```

New dependencies added:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data parsing

### 4. Frontend Configuration

The frontend automatically detects authentication. No additional configuration needed!

The frontend will:
- Redirect unauthenticated users to `/login`
- Store session in httpOnly cookies (secure)
- Show logout button in header
- Automatically include credentials in API calls

---

## 🔧 Deployment Instructions

### Render (Backend)

1. Go to your Render dashboard
2. Select your backend service
3. Navigate to **Environment** tab
4. Add the authentication environment variables:
   ```
   AUTH_ENABLED=true
   AUTH_USERNAME=your-username
   AUTH_PASSWORD=your-secure-password
   JWT_SECRET_KEY=your-generated-secret-key
   ```
4. Click **Save Changes**
5. Service will automatically redeploy

### Vercel (Frontend)

No changes needed! The frontend automatically adapts to the backend's authentication status.

However, ensure your `NEXT_PUBLIC_API_URL` points to your backend:

```bash
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api
```

---

## 🧪 Testing Authentication

### Test Login Flow

1. Navigate to your frontend URL
2. You should be redirected to `/login`
3. Enter your credentials (from `AUTH_USERNAME` and `AUTH_PASSWORD`)
4. You should be redirected to the home page
5. Your session should persist for 30 days

### Test Protected Endpoints

Try accessing the API directly:

```bash
# Without authentication - should return 401
curl https://your-backend.onrender.com/api/books

# With authentication - should return books
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://your-backend.onrender.com/api/books
```

### Test Logout

1. Click the logout button (top-right corner, next to theme toggle)
2. You should be redirected to `/login`
3. Session cookie should be cleared

---

## 🔐 Security Best Practices

### 1. Use Strong Credentials

❌ **Bad:**
```bash
AUTH_USERNAME=admin
AUTH_PASSWORD=password123
```

✅ **Good:**
```bash
AUTH_USERNAME=sugata_reader_2024
AUTH_PASSWORD=X9$mK2#pL8@vN4qR7!wE5
```

### 2. Use a Long Random JWT Secret

❌ **Bad:**
```bash
JWT_SECRET_KEY=mysecret
```

✅ **Good:**
```bash
JWT_SECRET_KEY=8f7d9c2e1a4b6f3e9d8c7a5b4e3f2d1c9b8a7e6d5c4b3a2f1e0d9c8b7a6f5e4d3
```

### 3. Enable HTTPS in Production

For production deployments, ensure HTTPS is enabled. Update the cookie settings in `app/api/auth.py`:

```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,  # ← Change this to True in production
    samesite="lax",
    # ...
)
```

### 4. Rotate JWT Secret Periodically

Change your `JWT_SECRET_KEY` every 3-6 months. This will invalidate all existing sessions (users will need to log in again).

---

## 🛠️ Advanced Configuration

### Disable Authentication (Development Only)

To disable authentication for local development:

```bash
AUTH_ENABLED=false
```

⚠️ **Warning:** Never deploy to production with authentication disabled!

### Change Token Expiration

Default session duration is 30 days. To change:

```bash
# 7 days
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 90 days
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=129600

# 1 day (for testing)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Custom JWT Algorithm

The default algorithm is `HS256`. To use a different algorithm:

```bash
JWT_ALGORITHM=HS512
```

Supported algorithms: `HS256`, `HS384`, `HS512`

---

## 🐛 Troubleshooting

### "Not authenticated" Error

**Symptoms:** API returns 401 Unauthorized

**Solutions:**
1. Check that `AUTH_ENABLED=true` is set
2. Verify `AUTH_USERNAME` and `AUTH_PASSWORD` are correct
3. Ensure JWT token hasn't expired
4. Clear browser cookies and log in again

### Login Page Not Showing

**Symptoms:** Redirected to blank page or 404

**Solutions:**
1. Ensure frontend middleware is working (`middleware.ts` exists)
2. Check that `/login` route exists (`app/login/page.tsx`)
3. Verify `NEXT_PUBLIC_API_URL` is set correctly

### Session Expires Too Quickly

**Symptoms:** Logged out after a few hours

**Solutions:**
1. Increase `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
2. Check server time is correct (JWT uses UTC)
3. Verify `JWT_SECRET_KEY` hasn't changed (this invalidates all tokens)

### CORS Errors

**Symptoms:** Browser console shows CORS errors

**Solutions:**
1. Ensure `FRONTEND_URL` is set correctly in backend
2. Verify `credentials: "include"` is set in frontend API calls
3. Check that `allow_credentials=True` in CORS middleware

---

## 📊 Architecture

### Authentication Flow

```
User → Frontend (Next.js)
  ↓
  Login Form → POST /api/auth/login
  ↓
  Backend (FastAPI) validates credentials
  ↓
  JWT token generated
  ↓
  Token stored in httpOnly cookie
  ↓
  Frontend redirects to home page
  ↓
  All API calls include cookie automatically
  ↓
  Backend validates token on each request
```

### Token Structure

JWT tokens contain:
```json
{
  "sub": "username",
  "exp": 1735689600
}
```

- `sub` (subject): The username
- `exp` (expiration): Unix timestamp when token expires

### Cookie Security

Cookies are configured with:
- `httpOnly=True` - Not accessible via JavaScript (prevents XSS)
- `samesite="lax"` - Prevents CSRF attacks
- `secure=True` (production) - Only sent over HTTPS
- `max_age` - Automatic expiration

---

## 🔄 Migration from Unauthenticated

If you're upgrading from an unauthenticated deployment:

1. **Backend:**
   - Update `requirements.txt` dependencies
   - Add authentication environment variables
   - Redeploy backend service

2. **Frontend:**
   - Pull latest code (includes login page and middleware)
   - Redeploy frontend (no env changes needed)

3. **First Login:**
   - Navigate to your app
   - You'll be redirected to login page
   - Enter credentials from environment variables
   - You're authenticated!

---

## 📚 API Reference

### POST `/api/auth/login`

Authenticate user and receive JWT token.

**Request:**
```json
{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "username": "your-username"
}
```

**Cookie Set:** `access_token` (httpOnly)

### POST `/api/auth/logout`

Logout user and clear session cookie.

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

### GET `/api/auth/verify`

Check if current session is authenticated.

**Response:**
```json
{
  "authenticated": true,
  "username": "your-username"
}
```

### GET `/api/auth/me`

Get current authenticated user info (requires authentication).

**Response:**
```json
{
  "username": "your-username"
}
```

---

## 💡 Future Enhancements

Potential future authentication features:

- **Multi-user support** - Multiple username/password pairs
- **Email OTP** - Passwordless authentication via email codes
- **OAuth2** - Login with GitHub, Google, etc.
- **Rate limiting** - Prevent brute force attacks
- **2FA** - Two-factor authentication
- **API keys** - Programmatic access for scripts

For now, the simple username/password system is perfect for personal use!

---

## ❓ FAQ

### Q: Can I share my library with friends?

A: Yes! Share your username and password with trusted friends. They can log in and access your library.

### Q: Can I have multiple users with separate libraries?

A: Not yet. The current system is single-user. Multi-user support would require:
- Separate B2 buckets per user
- User database
- More complex authentication

For now, it's designed for personal use or sharing with trusted individuals.

### Q: What happens if I forget my password?

A: Since credentials are stored in environment variables, you can:
1. Update `AUTH_PASSWORD` in your deployment settings
2. Redeploy the backend
3. Log in with the new password

There's no "forgot password" flow since it's a personal app.

### Q: Is my data encrypted?

A: Yes, in transit:
- HTTPS encrypts all communication (in production)
- JWT tokens are signed and verified
- Passwords are compared securely

However, data at rest (in B2) is not encrypted beyond B2's default encryption. For additional security, enable B2 server-side encryption.

### Q: Can I use this with multiple devices?

A: Yes! Log in on each device. Each device will have its own session cookie that lasts 30 days.

---

## 🎉 Summary

You now have a secure, personal library app with:

✅ Password-protected access to your reading data  
✅ Secure JWT-based sessions (30-day duration)  
✅ httpOnly cookies (XSS protection)  
✅ Simple username/password authentication  
✅ Clean login UI with shadcn components  
✅ Automatic session management  
✅ Easy deployment (just 3 environment variables)

Your highlights, annotations, and reading history are now private! 🔒📚

