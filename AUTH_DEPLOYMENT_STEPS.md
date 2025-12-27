# 🚀 Authentication Deployment Steps

## Quick Deployment Guide

Follow these steps to deploy authentication to your production environment.

---

## Step 1: Generate JWT Secret Key

Run this command on your local machine:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Output example:**
```
8f7d9c2e1a4b6f3e9d8c7a5b4e3f2d1c9b8a7e6d5c4b3a2f1e0d9c8b7a6f5e4d3
```

**Copy this output** - you'll need it in Step 2.

---

## Step 2: Configure Backend (Render)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Select your backend service (e.g., `highlights-fetch-service`)
3. Click **Environment** in the left sidebar
4. Click **Add Environment Variable**
5. Add these variables:

| Key | Value | Example |
|-----|-------|---------|
| `AUTH_ENABLED` | `true` | `true` |
| `AUTH_USERNAME` | Your username | `sugata` |
| `AUTH_PASSWORD` | Your password | `MySecureP@ssw0rd2024!` |
| `JWT_SECRET_KEY` | From Step 1 | `8f7d9c2e1a4b6f3e...` |

6. Click **Save Changes**
7. Render will automatically redeploy (takes ~2-3 minutes)

---

## Step 3: Verify Backend Deployment

Wait for deployment to complete, then test:

```bash
# Replace with your actual backend URL
curl https://your-backend.onrender.com/health
```

**Expected response:**
```json
{"status": "ok"}
```

---

## Step 4: Deploy Frontend (Vercel)

**Option A: Automatic (Recommended)**
1. Push your code to GitHub
2. Vercel will auto-deploy
3. Wait for deployment to complete (~1-2 minutes)

**Option B: Manual**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Click **Deployments** → **Redeploy**

---

## Step 5: Test Authentication

1. **Visit your app URL** (e.g., `https://readr.vercel.app`)
2. **You should be redirected to `/login`**
3. **Enter credentials:**
   - Username: (from Step 2)
   - Password: (from Step 2)
4. **Click "Login"**
5. **You should be redirected to home page**
6. **Verify logout button appears** (top-right, next to theme toggle)

---

## Step 6: Test Session Persistence

1. **Refresh the page** - you should stay logged in
2. **Close browser and reopen** - you should stay logged in
3. **Click logout button** - you should be redirected to `/login`
4. **Try accessing home page** - you should be redirected to `/login`

---

## Step 7: Test Protected Endpoints

```bash
# Replace with your actual backend URL
BACKEND_URL="https://your-backend.onrender.com"

# Should return 401 Unauthorized
curl $BACKEND_URL/api/books

# Should work after login (get token from browser cookies)
curl -H "Cookie: access_token=YOUR_TOKEN" $BACKEND_URL/api/books
```

---

## ✅ Deployment Checklist

- [ ] Generated JWT secret key
- [ ] Added all 4 environment variables to Render
- [ ] Backend redeployed successfully
- [ ] Frontend redeployed successfully
- [ ] Can access login page
- [ ] Can login with credentials
- [ ] Redirected to home after login
- [ ] Logout button appears
- [ ] Session persists across refreshes
- [ ] Logout works correctly
- [ ] Protected endpoints require auth

---

## 🔐 Security Checklist

- [ ] Used strong password (16+ characters)
- [ ] Used generated JWT secret (not a simple string)
- [ ] Saved credentials securely (password manager)
- [ ] Verified HTTPS is enabled (production)
- [ ] Tested in incognito/private mode
- [ ] Shared credentials only with trusted people (if applicable)

---

## 🐛 Troubleshooting

### "Not authenticated" error

**Cause:** Invalid credentials or JWT token

**Solution:**
1. Verify `AUTH_USERNAME` and `AUTH_PASSWORD` in Render
2. Check JWT_SECRET_KEY is set correctly
3. Clear browser cookies and try again
4. Check browser console for errors

### Login page not showing

**Cause:** Frontend not deployed or middleware not working

**Solution:**
1. Verify frontend deployed successfully
2. Check `middleware.ts` exists in project
3. Verify `NEXT_PUBLIC_API_URL` is set correctly
4. Check browser console for errors

### Session expires immediately

**Cause:** JWT secret mismatch or cookie issues

**Solution:**
1. Verify `JWT_SECRET_KEY` matches between deployments
2. Check browser allows cookies
3. Verify CORS settings in backend
4. Check `credentials: "include"` in frontend API calls

### CORS errors

**Cause:** Frontend URL not allowed by backend

**Solution:**
1. Add your frontend URL to `FRONTEND_URL` env var in backend
2. Format: `https://readr.vercel.app,https://www.readr.vercel.app`
3. Redeploy backend

---

## 📞 Need Help?

See detailed troubleshooting in:
- [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) - Complete guide
- [AUTHENTICATION_IMPLEMENTATION.md](./AUTHENTICATION_IMPLEMENTATION.md) - Technical details

---

## 🎉 Success!

If all steps passed, your authentication is now live! 🔒

Your personal reading data is protected from public access.

**Next Steps:**
1. Save your credentials securely
2. Consider rotating JWT secret every 3-6 months
3. Monitor backend logs for any issues
4. Enjoy your private reading library! 📚

---

**Deployment Date:** _________________  
**Backend URL:** _________________  
**Frontend URL:** _________________  
**Status:** [ ] Complete

