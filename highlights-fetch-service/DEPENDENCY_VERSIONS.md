# Dependency Version Management

## 📋 Overview

All dependencies in `requirements.txt` are **bounded** to prevent breaking changes from automatic upgrades while still allowing security patches and minor updates.

**Last Updated**: January 8, 2025

---

## 🔒 Versioning Strategy

### **Format: `package>=MIN_VERSION,<MAX_VERSION`**

- **Lower bound** (`>=`): Minimum tested version with required features
- **Upper bound** (`<`): Excludes major versions with potential breaking changes
- **Allows**: Patch and minor updates for security and bug fixes

---

## 📦 Core Dependencies

| Package | Version Range | Rationale |
|---------|---------------|-----------|
| `fastapi` | `>=0.104.0,<0.115.0` | Lock to 0.1xx series, allow minor updates |
| `uvicorn[standard]` | `>=0.24.0,<0.31.0` | Tested with 0.24-0.30, block 0.31+ breaking changes |
| `b2sdk` | `>=1.0.0,<3.0.0` | Allow 1.x and 2.x, block 3.x major changes |
| `pydantic` | `>=2.0.0,<3.0.0` | Lock to Pydantic 2.x (breaking changes in 3.x) |
| `pydantic-settings` | `>=2.0.0,<3.0.0` | Must match Pydantic major version |
| `python-dotenv` | `>=0.19.0,<2.0.0` | Stable API, allow 1.x updates |
| `sqlalchemy` | `>=1.4.0,<3.0.0` | Support both 1.4+ and 2.x |
| `requests` | `>=2.28.0,<3.0.0` | Stable 2.x API |

---

## 🔐 Security Dependencies (Pinned)

These are **exact versions** for security and reproducibility:

| Package | Version | Rationale |
|---------|---------|-----------|
| `python-jose[cryptography]` | `==3.5.0` | JWT handling - exact version for security |
| `passlib[bcrypt]` | `==1.7.4` | Password hashing - tested version |
| `bcrypt` | `==4.1.3` | Specific version for passlib 1.7.4 compatibility |
| `python-multipart` | `==0.0.21` | Form parsing - stable version |

⚠️ **Note**: Security packages are pinned to exact versions. Update only after security audits.

---

## 🤖 AI Companion Dependencies

| Package | Version Range | Rationale |
|---------|---------------|-----------|
| `python-telegram-bot` | `>=20.0,<22.0` | Lock to v20-21, block v22 breaking changes |
| `google-generativeai` | `==0.8.3` | Pinned (DEPRECATED - migrate by Nov 2025) |

⚠️ **Migration Required**: See `MIGRATION_TODO.md` for Google Gemini SDK migration plan.

---

## 🔄 Update Guidelines

### **When to Update Dependencies**

1. **Security patches**: Update immediately if CVE announced
2. **Bug fixes**: Update within minor version range
3. **New features**: Evaluate need vs. risk before updating
4. **Major versions**: Requires testing and approval

### **How to Update**

```bash
# 1. Check current versions
pip list

# 2. Check for updates within bounds
pip list --outdated

# 3. Update specific package (stays within bounds)
pip install --upgrade fastapi

# 4. Test thoroughly
pytest

# 5. Update requirements.txt if needed
pip freeze > requirements-frozen.txt
```

### **Testing Checklist Before Update**

- [ ] Run all tests: `pytest`
- [ ] Check linter: `mypy`, `flake8`, etc.
- [ ] Test locally: Run the app and verify functionality
- [ ] Test in staging: Deploy to staging environment
- [ ] Monitor logs: Check for warnings or errors
- [ ] Update docs: If API changes, update documentation

---

## 🚨 Breaking Change Policy

### **What Constitutes a Breaking Change?**

- Removed or renamed APIs
- Changed function signatures
- Modified return types
- Deprecated features removed
- Major version bumps (e.g., 1.x → 2.x)

### **If a Breaking Change is Needed**

1. **Research**: Read changelog and migration guide
2. **Test**: Create isolated test environment
3. **Update code**: Adapt to new API
4. **Update bounds**: Adjust version ranges
5. **Document**: Update this file and release notes
6. **Deploy**: Stage → Production with monitoring

---

## 📊 Dependency Audit Schedule

| Action | Frequency | Responsible |
|--------|-----------|-------------|
| Security updates | Immediate | DevOps/Security team |
| Minor updates | Monthly | Development team |
| Major updates | Quarterly | Tech lead + team |
| Full audit | Bi-annually | All stakeholders |

---

## 🔍 Current Known Issues

### **Deprecations**

1. **`google-generativeai` (0.8.3)**
   - **Status**: DEPRECATED
   - **Deadline**: November 30, 2025
   - **Action**: Migrate to `google-genai`
   - **Details**: See `MIGRATION_TODO.md`

### **Upcoming Breaking Changes**

None currently known (as of Jan 2025).

---

## 📚 Resources

- **FastAPI Changelog**: https://fastapi.tiangolo.com/release-notes/
- **Pydantic Changelog**: https://docs.pydantic.dev/latest/changelog/
- **Uvicorn Changelog**: https://www.uvicorn.org/changelog/
- **Python Telegram Bot**: https://github.com/python-telegram-bot/python-telegram-bot/releases
- **Security Advisories**: https://github.com/advisories

---

## 🎯 Version Compatibility Matrix

| Python | FastAPI | Pydantic | Uvicorn | Status |
|--------|---------|----------|---------|--------|
| 3.11   | 0.104+  | 2.x      | 0.24+   | ✅ Tested |
| 3.12   | 0.104+  | 2.x      | 0.24+   | ✅ Tested |
| 3.13   | 0.104+  | 2.x      | 0.24+   | ⚠️ Not tested |

---

## ✅ Maintenance Checklist

### Monthly
- [ ] Check for security advisories
- [ ] Update patch versions within bounds
- [ ] Review deprecation warnings in logs

### Quarterly
- [ ] Review and update version bounds
- [ ] Test with latest minor versions
- [ ] Update this documentation

### Annually
- [ ] Full dependency audit
- [ ] Evaluate major version upgrades
- [ ] Review and update versioning strategy

---

**Maintained by**: Development Team  
**Last Review**: January 8, 2025  
**Next Review**: April 2025

