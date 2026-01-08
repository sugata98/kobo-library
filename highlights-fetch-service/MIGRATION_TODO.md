# Migration TODO: Google Gemini SDK

## ⚠️ CRITICAL: Migrate by November 30, 2025

### Current Status

- **Current SDK**: `google-generativeai` (v0.8.3) - DEPRECATED
- **New SDK**: `google-genai` (Cloud-based SDK)
- **Deadline**: November 30, 2025
- **Priority**: Medium (have ~10 months as of Jan 2025)

---

## 📋 Migration Checklist

### Phase 1: Research & Planning (Before Q2 2025)

- [ ] Review migration guide: https://ai.google.dev/gemini-api/docs/migrate-to-cloud
- [ ] Test `google-genai` SDK in development
- [ ] Identify breaking changes in API
- [ ] Update AI companion service code
- [ ] Test with Gemini 3 Flash Preview model

### Phase 2: Implementation (Q3 2025)

- [ ] Update `requirements.txt`: Remove `google-generativeai==0.8.3`, add `google-genai`
- [ ] Update `app/services/kobo_ai_companion.py`: Replace imports and API calls
- [ ] Update configuration if needed (model names, API keys)
- [ ] Test locally with real highlights
- [ ] Update documentation

### Phase 3: Testing & Deployment (Q3 2025)

- [ ] Test in staging environment
- [ ] Verify webhook integration still works
- [ ] Test conversation mode (follow-up questions)
- [ ] Deploy to production
- [ ] Monitor for issues

### Phase 4: Cleanup (Q4 2025, before deadline)

- [ ] Remove old SDK completely
- [ ] Update IMPLEMENTATION_SUMMARY.md
- [ ] Update README references
- [ ] Delete this migration TODO file

---

## 🔄 Code Changes Required

### Files to Update:

1. **`requirements.txt`**

   ```bash
   # Remove:
   google-generativeai==0.8.3

   # Add:
   google-genai>=1.0.0,<2.0.0
   ```

2. **`app/services/kobo_ai_companion.py`**

   ```python
   # Change imports from:
   import google.generativeai as genai

   # To:
   from google import genai

   # Update API calls according to new SDK patterns
   ```

3. **Configuration** (if needed)
   - Check if `GEMINI_API_KEY` format changes
   - Verify model naming (e.g., `gemini-3-flash-preview` vs new names)

---

## 📚 Resources

- **Migration Guide**: https://ai.google.dev/gemini-api/docs/migrate-to-cloud
- **New SDK Docs**: https://googleapis.github.io/python-genai/
- **Changelog**: https://github.com/googleapis/python-genai/releases
- **Support Forum**: https://discuss.ai.google.dev/

---

## 🚨 Risk Assessment

**Risk**: Medium

- Legacy SDK works until Nov 30, 2025
- Migration is straightforward (mostly import changes)
- New SDK likely has similar API patterns

**Mitigation**:

- Start testing in Q2 2025
- Run both SDKs in parallel during testing
- Keep rollback plan ready

---

## 📅 Timeline

| Date     | Action                   |
| -------- | ------------------------ |
| Jan 2025 | Added migration TODO     |
| Q2 2025  | Research & test new SDK  |
| Q3 2025  | Implement & deploy       |
| Nov 2025 | Complete before deadline |

---

**Last Updated**: January 8, 2025  
**Owner**: Development Team  
**Status**: Pending (scheduled for Q2/Q3 2025)
