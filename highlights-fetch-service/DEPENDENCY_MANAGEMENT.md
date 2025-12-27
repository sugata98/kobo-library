# Dependency Management & Security

## Pinned Security Packages

The authentication and cryptography packages are **pinned to specific versions** for security and reproducibility:

| Package                     | Version | Purpose            | Notes                                                                                       |
| --------------------------- | ------- | ------------------ | ------------------------------------------------------------------------------------------- |
| `python-jose[cryptography]` | 3.5.0   | JWT token handling | Latest stable, includes cryptography backend for secure signing                             |
| `passlib[bcrypt]`           | 1.7.4   | Password hashing   | Latest stable, widely used and audited                                                      |
| `bcrypt`                    | 4.1.3   | Bcrypt backend     | **Critical**: Pinned for compatibility with passlib 1.7.4 (bcrypt 5.x breaks compatibility) |
| `python-multipart`          | 0.0.21  | Form data parsing  | Latest stable, required for FastAPI form handling                                           |

## Why Pin Dependencies?

### Security Benefits

1. **Prevent Supply Chain Attacks**: Pinned versions ensure you're installing known, audited code
2. **Reproducible Builds**: Same versions across dev, test, and production environments
3. **Controlled Updates**: Update dependencies intentionally, with testing
4. **Audit Trail**: Clear record of what versions are deployed

### Compatibility

- **bcrypt compatibility issue**: passlib 1.7.4 (released 2018) is not compatible with bcrypt 5.x (released 2024)
- Pinning bcrypt to 4.1.3 ensures compatibility while maintaining security

## Version Selection Criteria

Versions were selected based on:

1. **Latest stable releases** (as of Dec 2024)
2. **Security audit status** - no known vulnerabilities
3. **Compatibility testing** - verified to work together
4. **Community adoption** - widely used versions

## PyPI Verification

All pinned versions verified on PyPI:

```bash
# Check available versions
python -m pip index versions python-jose
python -m pip index versions passlib
python -m pip index versions bcrypt
python -m pip index versions python-multipart
```

## Testing Pinned Versions

### Basic Functionality Test

```python
# Test JWT handling
from jose import jwt
import secrets

secret = secrets.token_urlsafe(32)
token = jwt.encode({'sub': 'test'}, secret, algorithm='HS256')
decoded = jwt.decode(token, secret, algorithms=['HS256'])
print(f"✓ JWT: {decoded['sub']}")

# Test password hashing (if using bcrypt)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
hashed = pwd_context.hash('test_password')
verified = pwd_context.verify('test_password', hashed)
print(f"✓ Bcrypt: {verified}")
```

### Run Config Validation

```bash
python test_config_validation.py
```

## Current Authentication Implementation

**Note**: The current app uses **simple password comparison** for single-user personal use:

```python
# From app/core/auth.py
return password == settings.AUTH_PASSWORD.get_secret_value()
```

- ✅ Acceptable for single-user personal apps
- ✅ Passwords stored as secrets (never logged)
- ⚠️ For multi-user production, use `passlib` bcrypt hashing (functions already implemented)

## Recommended: Pin All Dependencies

Currently, **only security-critical packages are pinned**. For production, consider pinning ALL dependencies:

### Option 1: Manual Pinning (requirements.txt)

Generate pinned versions from current environment:

```bash
pip freeze > requirements-frozen.txt
```

Then manually review and update `requirements.txt`:

```txt
fastapi==0.115.6
uvicorn==0.34.0
b2sdk==2.7.0
pydantic==2.10.5
pydantic-settings==2.7.1
python-dotenv==1.0.1
sqlalchemy==2.0.37
requests==2.32.3
# Security packages (already pinned)
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.3
python-multipart==0.0.21
```

### Option 2: Use pip-tools (Recommended for Production)

Install pip-tools:

```bash
pip install pip-tools
```

Create `requirements.in` with high-level dependencies:

```txt
fastapi
uvicorn
b2sdk
pydantic
pydantic-settings
python-dotenv
sqlalchemy
requests
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.3
python-multipart==0.0.21
```

Generate locked requirements:

```bash
pip-compile requirements.in
```

This creates `requirements.txt` with all dependencies (including transitive ones) pinned.

Install from locked file:

```bash
pip-sync requirements.txt
```

**Benefits:**

- Pins ALL dependencies, including transitive ones
- Easy to update: `pip-compile --upgrade`
- Separate concerns: `.in` for what you want, `.txt` for exact versions

### Option 3: Use Poetry (Modern Alternative)

Initialize Poetry:

```bash
poetry init
poetry add fastapi uvicorn b2sdk pydantic pydantic-settings python-dotenv sqlalchemy requests
poetry add "python-jose[cryptography]==3.5.0" "passlib[bcrypt]==1.7.4" "bcrypt==4.1.3" "python-multipart==0.0.21"
```

**Benefits:**

- Automatic lock file (`poetry.lock`)
- Built-in virtual environment management
- Dependency resolution and conflict detection
- Dev vs. production dependencies

## Security Scanning

Regularly scan for vulnerabilities:

```bash
# Install pip-audit
pip install pip-audit

# Scan dependencies
pip-audit

# Or with poetry
poetry export -f requirements.txt | pip-audit -r /dev/stdin
```

## Update Strategy

### Regular Updates

1. **Security patches**: Update immediately after testing
2. **Minor versions**: Monthly review
3. **Major versions**: Quarterly review with thorough testing

### Update Process

1. Check for updates: `pip list --outdated`
2. Review changelogs for breaking changes
3. Update in development environment
4. Run full test suite
5. Deploy to staging
6. Deploy to production

### For Security Packages

```bash
# Check for security advisories
pip-audit

# Update specific package
pip install --upgrade python-jose[cryptography]

# Or with pip-tools
pip-compile --upgrade-package python-jose
```

## Hash Pinning (Maximum Security)

For maximum security, use hash pinning to verify package integrity:

```bash
# Generate requirements with hashes
pip-compile --generate-hashes requirements.in

# Install with hash verification
pip install --require-hashes -r requirements.txt
```

Example with hashes:

```txt
python-jose[cryptography]==3.5.0 \
    --hash=sha256:abcdef123456...
passlib[bcrypt]==1.7.4 \
    --hash=sha256:123456abcdef...
```

**Benefits:**

- Verifies package hasn't been tampered with
- Detects compromised packages on PyPI
- Meets compliance requirements for high-security environments

## Compatibility Matrix

Tested and verified combinations:

| Python | python-jose | passlib | bcrypt | Status              |
| ------ | ----------- | ------- | ------ | ------------------- |
| 3.10.x | 3.5.0       | 1.7.4   | 4.1.3  | ✅ Tested           |
| 3.11.x | 3.5.0       | 1.7.4   | 4.1.3  | ✅ Expected to work |
| 3.12.x | 3.5.0       | 1.7.4   | 4.1.3  | ✅ Expected to work |

**Note**: Avoid bcrypt 5.x with passlib 1.7.4 - known compatibility issues.

## Troubleshooting

### Issue: bcrypt version errors

**Error**: `AttributeError: module 'bcrypt' has no attribute '__about__'`

**Solution**: Ensure bcrypt is pinned to 4.1.3 (not 5.x):

```bash
pip install bcrypt==4.1.3
```

### Issue: Conflicting dependencies

**Solution**: Use pip-tools or Poetry to resolve conflicts automatically:

```bash
pip-compile --resolver=backtracking
```

### Issue: Hash verification failures

**Solution**: Regenerate hashes after updating packages:

```bash
pip-compile --generate-hashes requirements.in
```

## References

- [PyPI - python-jose](https://pypi.org/project/python-jose/)
- [PyPI - passlib](https://pypi.org/project/passlib/)
- [PyPI - bcrypt](https://pypi.org/project/bcrypt/)
- [PyPI - python-multipart](https://pypi.org/project/python-multipart/)
- [pip-tools Documentation](https://github.com/jazzband/pip-tools)
- [Poetry Documentation](https://python-poetry.org/)
- [pip-audit](https://github.com/pypa/pip-audit)

## Related Documentation

- `SECURITY_IMPROVEMENTS.md` - Security configuration details
- `SECURITY_CHANGES_SUMMARY.md` - Summary of security changes
- `requirements.txt` - Pinned dependencies
- `test_config_validation.py` - Validation test suite
