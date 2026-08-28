# Security Audit Report & Fixes - PRAP Backend

## Executive Summary
This document outlines critical security vulnerabilities identified in the PRAP Backend codebase and the fixes implemented to address them.

---

## Critical Security Issues Found & Fixed

### 1. **Question Endpoint - Unauthorized Access (CRITICAL)**
**Issue**: GET requests to `/api/questions/` allowed anyone to view all questions without authentication.  
**Impact**: Students could potentially see all questions before taking the exam, compromising assessment integrity.  
**Fix**: Changed `QuestionListCreateView` to require `IsAdminUser` permission for all methods (GET, POST, etc.)  
**File**: `api/views.py` - Line 162-175

**Before:**
```python
def get_permissions(self):
    if self.request.method == 'GET':
        return [permissions.AllowAny()]
    return [IsAdminUser()]
```

**After:**
```python
permission_classes = [IsAdminUser]
```

---

### 2. **Hardcoded Credentials (CRITICAL)**
**Issue**: Email password and SECRET_KEY exposed in `settings.py`  
**Impact**: If code is leaked or repository is public, attackers gain access to email account and can sign JWT tokens.  
**Fix**: 
- Moved all sensitive data to environment variables
- Created `.env.example` file as template
- Added `python-dotenv` to requirements.txt  
**Files**: `prap_backend/settings.py`, `.env.example`, `requirements.txt`

**Environment Variables Added:**
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `CORS_ALLOWED_ORIGINS`
- Security settings for production

---

### 3. **Insecure Password Storage (CRITICAL)**
**Issue**: Passwords stored in plain text in `StudentProfile.password` field  
**Impact**: If database is compromised, all student passwords are exposed.  
**Fix**: 
- Removed `password` field from `StudentProfile` model
- Passwords now stored securely in Django's `User` model (hashed using PBKDF2)
- Updated serializers and views to use User authentication  
**Files**: `api/models.py`, `api/serializers.py`, `api/views.py`

**Migration Required**: Run `python manage.py makemigrations` and `python manage.py migrate` to remove the password column from database.

---

### 4. **Exam Submission - No Authentication (HIGH)**
**Issue**: `StudentExamSubmitView` allowed unauthenticated exam submission  
**Impact**: Anyone could submit fake exam results.  
**Fix**: 
- Added validation to ensure student exists in database
- Added optional resume token verification
- Removed fallback profile creation  
**File**: `api/views.py` - Line 535-604

---

### 5. **Exam Results - No Authentication (HIGH)**
**Issue**: `StudentExamResultsView` allowed anyone to view results with just a mobile number  
**Impact**: Students could view other students' results if they knew their mobile number.  
**Fix**: Added validation to ensure mobile number belongs to a registered student  
**File**: `api/views.py` - Line 607-656

---

### 6. **Permissive CORS Configuration (MEDIUM)**
**Issue**: `CORS_ALLOW_ALL_ORIGINS = True` allowed any origin  
**Impact**: Enables cross-origin attacks from any website.  
**Fix**: 
- Changed to specific allowed origins from environment variable
- Set `CORS_ALLOW_CREDENTIALS = True`  
**File**: `prap_backend/settings.py`

---

### 7. **Overly Permissive ALLOWED_HOSTS (MEDIUM)**
**Issue**: `ALLOWED_HOSTS = ['*']` allowed any host  
**Impact**: Enables host header attacks.  
**Fix**: Changed to read from environment variable with default to localhost  
**File**: `prap_backend/settings.py`

---

### 8. **Default REST Framework Permissions (MEDIUM)**
**Issue**: `DEFAULT_PERMISSION_CLASSES` set to `AllowAny`  
**Impact**: All endpoints default to no authentication required.  
**Fix**: Changed to `IsAuthenticated` and added rate limiting  
**File**: `prap_backend/settings.py`

---

### 9. **Excessive JWT Token Lifetime (MEDIUM)**
**Issue**: Access tokens valid for 1 day  
**Impact**: If token is stolen, attacker has access for 24 hours.  
**Fix**: 
- Reduced access token lifetime to 2 hours
- Enabled refresh token rotation
- Enabled blacklist after rotation  
**File**: `prap_backend/settings.py`

---

### 10. **Missing Production Security Headers (LOW)**
**Issue**: No security headers for production environment  
**Impact**: Vulnerable to various web attacks.  
**Fix**: Added conditional security settings for production:
- SSL redirect
- Secure cookies
- XSS protection
- Content type sniffing protection
- Frame options (DENY)
- HSTS headers  
**File**: `prap_backend/settings.py`

---

## Installation Instructions

### 1. Install New Dependencies
```bash
pip install python-dotenv
```

### 2. Create Environment File
```bash
copy .env.example .env
```

### 3. Update .env with Your Values
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
CORS_ALLOWED_ORIGINS=https://your-frontend.com
```

### 4. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

---

## Security Best Practices Implemented

1. **Environment-based configuration** - No hardcoded secrets
2. **Secure password storage** - Using Django's built-in password hashing
3. **Token-based authentication** - JWT with reasonable expiration
4. **Role-based access control** - Admin vs Student permissions
5. **Rate limiting** - Preventing API abuse
6. **CORS restrictions** - Only allowed origins
7. **Security headers** - Production-ready security settings
8. **Input validation** - Mobile number and email validation

---

## Testing Recommendations

1. **Test admin endpoints** - Ensure only admins can access `/api/questions/`, `/api/districts/`, etc.
2. **Test student authentication** - Verify students can login and access their data
3. **Test CORS** - Verify only allowed origins can access the API
4. **Test exam submission** - Ensure only registered students can submit exams
5. **Test results access** - Ensure students can only see their own results
6. **Test environment variables** - Verify app works with .env configuration

---

## Additional Security Recommendations

1. **Implement HTTPS** - Use SSL in production
2. **Add CSRF protection** - For any form submissions
3. **Implement logging** - Track authentication attempts and suspicious activity
4. **Add input sanitization** - Prevent SQL injection and XSS
5. **Regular security audits** - Periodically review dependencies and code
6. **Backup strategy** - Regular database backups with encryption
7. **API versioning** - Maintain backward compatibility while improving security

---

## Migration Note

The removal of the `password` field from `StudentProfile` requires a database migration. If you have existing student data:

**Option 1: Run migration** (Recommended for new deployments)
```bash
python manage.py makemigrations
python manage.py migrate
```

**Option 2: Skip migration** (If you want to preserve existing password column temporarily)
- Keep the field in the model but mark it as deprecated
- Plan for data migration later

**Option 3: Use previous version** (If you have working version from previous session)
- Copy the migrations from your previous session folder
- Ensure the database schema matches the model

---

## Contact & Support

For questions about these security fixes, please refer to:
- Django Security Documentation: https://docs.djangoproject.com/en/stable/topics/security/
- DRF Authentication: https://www.django-rest-framework.org/api-guide/authentication/
- JWT Documentation: https://django-rest-framework-simplejwt.readthedocs.io/