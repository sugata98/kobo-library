# 🚀 Quick Start: Authentication

## 5-Minute Setup

### Step 1: Generate JWT Secret

Run this command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output (something like: `8f7d9c2e1a4b6f3e9d8c7a5b4e3f2d1c9b8a7e6d5c4b3a2f1e0d9c8b7a6f5e4d3`)

### Step 2: Add Environment Variables

**Backend (Render):**

Go to your Render service → Environment → Add:

```
AUTH_ENABLED=true
AUTH_USERNAME=your-username
AUTH_PASSWORD=your-secure-password
JWT_SECRET_KEY=<paste-from-step-1>
```

**Frontend (Vercel):**

No changes needed! ✨

### Step 3: Deploy

Save environment variables in Render. Service will auto-deploy.

### Step 4: Login

1. Visit your app URL
2. You'll be redirected to `/login`
3. Enter your username and password from Step 2
4. You're in! 🎉

Session lasts 30 days.

---

## Disable Authentication (Development)

```bash
AUTH_ENABLED=false
```

---

## Troubleshooting

**"Not authenticated" error?**

- Check username/password are correct
- Verify JWT_SECRET_KEY is set
- Clear browser cookies and try again

**Login page not showing?**

- Ensure frontend is deployed with latest code
- Check NEXT_PUBLIC_API_URL is correct

**Need help?**
See [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) for detailed guide.

---

## What's Protected?

✅ Your book list  
✅ Your highlights  
✅ Your annotations  
✅ Your handwritten markups  
✅ Your reading progress

❌ Book covers (public, no personal data)

---

## Security Tips

1. **Use a strong password** (16+ characters, mix of letters/numbers/symbols)
2. **Use a long JWT secret** (generated, not guessed)
3. **Don't share credentials** (unless with trusted friends)
4. **Rotate JWT secret** every 3-6 months

---

That's it! Your personal reading data is now protected. 🔒📚
