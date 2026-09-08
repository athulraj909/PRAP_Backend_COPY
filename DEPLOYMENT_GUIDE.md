# PRAP Backend - Production Deployment Guide

## Environment Details
- **Backend**: Django REST Framework hosted on PythonAnywhere
- **Backend URL**: https://oneteamprap.pythonanywhere.com/
- **Frontend**: Vercel deployment
- **Frontend URL**: https://prapfrontendhosted.vercel.app

---

## Pre-Deployment Checklist

### 1. Environment Configuration
- [ ] Copy `.env.production` to `.env` on PythonAnywhere
- [ ] Update SECRET_KEY with a strong random key (min 50 characters)
- [ ] Update EMAIL_HOST_PASSWORD with Gmail app password
- [ ] Verify ALLOWED_HOSTS includes your PythonAnywhere domain
- [ ] Verify CORS_ALLOWED_ORIGINS includes your Vercel frontend URL

### 2. Security Setup
- [ ] Generate strong SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- [ ] Create Gmail app password for email functionality
- [ ] Configure SSL/HTTPS on PythonAnywhere
- [ ] Set DEBUG=False in production

### 3. Database Setup
- [ ] Choose between SQLite (default) or PostgreSQL (recommended for production)
- [ ] If using PostgreSQL, set up database on PythonAnywhere
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser if needed: `python manage.py createsuperuser`

---

## PythonAnywhere Deployment Steps

### Step 1: Upload Code to PythonAnywhere

1. **Clone or upload your repository**
   ```bash
   # On PythonAnywhere bash console
   cd ~
   git clone your-repo-url prap_backend
   cd prap_backend
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Configure Environment Variables

1. **Create .env file**
   ```bash
   nano .env
   ```

2. **Add the following content** (update with your actual values):
   ```env
   DEBUG=False
   SECRET_KEY=your-generated-secret-key-here-min-50-chars
   ALLOWED_HOSTS=oneteamprap.pythonanywhere.com
   EMAIL_HOST_USER=oneteamprap@gmail.com
   EMAIL_HOST_PASSWORD=your-gmail-app-password
   CORS_ALLOWED_ORIGINS=https://prapfrontendhosted.vercel.app
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

3. **Generate SECRET_KEY** (if not already):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

### Step 3: Database Setup

**Option A: SQLite (Default)**
```bash
python manage.py migrate
```

**Option B: PostgreSQL (Recommended for Production)**
1. Create PostgreSQL database on PythonAnywhere
2. Update .env with database credentials:
   ```env
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=your-db-name
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   DB_HOST=your-db-host.pythonanywhere.com
   DB_PORT=5432
   ```
3. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```

### Step 4: Configure Web Application

1. **Go to PythonAnywhere Web tab**
2. **Add a new web app**
3. **Choose Manual Configuration** (recommended) or Django
4. **Configure the following:**

**For Manual Configuration:**
- **Source code**: `/home/oneteamprap/prap_backend`
- **Working directory**: `/home/oneteamprap/prap_backend`
- **WSGI configuration file**: `/home/oneteamprap/prap_backend/prap_backend/wsgi.py`

**Update wsgi.py** (if needed):
```python
import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to Python path
sys.path.insert(0, '/home/oneteamprap/prap_backend')

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prap_backend.settings')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/home/oneteamprap/prap_backend/.env')

application = get_wsgi_application()
```

**Virtualenv**: `/home/oneteamprap/prap_backend/venv`

### Step 5: Configure Static Files

1. **Create static files directory**
   ```bash
   mkdir -p /home/oneteamprap/prap_backend/static
   ```

2. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Configure static files in PythonAnywhere Web tab**
   - **Static files URL**: `/static/`
   - **Static files directory**: `/home/oneteamprap/prap_backend/static`

### Step 6: Configure Security

1. **Enable SSL/HTTPS** in PythonAnywhere Web tab
2. **Force HTTPS** by setting `SECURE_SSL_REDIRECT=True` in .env
3. **Configure domain** to point to your PythonAnywhere app

### Step 7: Test the Deployment

1. **Reload web app** in PythonAnywhere
2. **Test API endpoints**:
   ```bash
   curl https://oneteamprap.pythonanywhere.com/api/public/districts/
   ```
3. **Check error logs** in PythonAnywhere if issues occur

---

## Security Middleware Configuration

The application includes comprehensive security middleware:

### 1. Security Headers Middleware
- Content Security Policy (CSP)
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options (DENY)
- X-XSS-Protection
- X-Content-Type-Options

### 2. Rate Limiting Middleware
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Configurable via environment variables

### 3. IP Security Middleware
- Failed login attempt tracking
- Automatic IP blocking after 5 failed attempts
- Suspicious activity detection (SQL injection, XSS patterns)
- Configurable whitelist/blacklist

### 4. Request Validation Middleware
- User-Agent validation
- Content-Type validation
- Request size limits (10MB default)
- Referer origin validation

---

## Frontend Configuration (Vercel)

### 1. Environment Variables in Vercel

Set these in your Vercel project settings:

```env
NEXT_PUBLIC_API_URL=https://oneteamprap.pythonanywhere.com/api
NEXT_PUBLIC_APP_URL=https://prapfrontendhosted.vercel.app
```

### 2. CORS Configuration

The backend is already configured to allow requests from:
- `https://prapfrontendhosted.vercel.app`

### 3. API Endpoints

Your frontend should use these endpoints:

```javascript
const API_BASE_URL = 'https://oneteamprap.pythonanywhere.com/api';

// Public endpoints
GET /public/districts/
GET /public/colleges/
GET /public/courses/
GET /public/assessment-categories/
GET /public/exam-settings/

// Student endpoints
POST /student/register/
POST /student/login/
GET /student/profile/ (requires auth)
POST /student/exam/submit/
GET /student/exam/results/?mobile=1234567890

// Admin endpoints (requires admin auth)
POST /api/admin/login/
GET /districts/
POST /districts/
GET /questions/
POST /questions/
GET /dashboard/stats/
```

---

## Monitoring and Maintenance

### 1. Log Monitoring

Monitor logs in PythonAnywhere:
- **Error logs**: `/var/log/oneteamprap.error.log`
- **Access logs**: `/var/log/oneteamprap.access.log`
- **Application logs**: Check for security middleware warnings

### 2. Database Backups

**For SQLite:**
```bash
# Backup
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)

# Restore
cp db.sqlite3.backup.YYYYMMDD db.sqlite3
```

**For PostgreSQL:**
Use PythonAnywhere's built-in backup tools or pg_dump.

### 3. Regular Maintenance Tasks

- **Update dependencies**: `pip install --upgrade -r requirements.txt`
- **Check security advisories**: `pip check`
- **Review and rotate secrets** periodically
- **Monitor rate limiting** and adjust if needed
- **Review blocked IPs** and whitelist legitimate users

---

## Troubleshooting

### Common Issues

**1. 500 Internal Server Error**
- Check error logs in PythonAnywhere
- Verify .env file exists and has correct permissions
- Ensure all dependencies are installed
- Check database migrations are up to date

**2. CORS Errors**
- Verify CORS_ALLOWED_ORIGINS includes your frontend URL
- Check frontend is making requests with correct origin
- Ensure SSL/HTTPS is properly configured

**3. Authentication Issues**
- Verify JWT configuration in settings
- Check SECRET_KEY is the same across all environments
- Ensure token lifetime is appropriate

**4. Rate Limiting Issues**
- Adjust RATE_LIMIT_ANON and RATE_LIMIT_USER in .env
- Check cache configuration for rate limiting
- Review blocked IPs in logs

**5. Email Issues**
- Verify Gmail app password is correct
- Check EMAIL_HOST and EMAIL_PORT settings
- Ensure PythonAnywhere allows outbound SMTP

---

## Security Best Practices

### 1. Regular Security Audits
- Review Django security advisories
- Check for vulnerabilities in dependencies
- Monitor authentication logs for suspicious activity

### 2. Access Control
- Use strong passwords for admin accounts
- Enable two-factor authentication if available
- Regularly review user access and permissions

### 3. Data Protection
- Regular database backups
- Encrypt sensitive data at rest
- Use HTTPS for all communications

### 4. Monitoring
- Set up alerts for failed authentication attempts
- Monitor API usage patterns
- Track blocked IPs and suspicious activity

---

## Performance Optimization

### 1. Database Optimization
- Use PostgreSQL for production (better performance than SQLite)
- Add database indexes for frequently queried fields
- Optimize queries with select_related/prefetch_related

### 2. Caching
- Configure Redis or Memcached for production caching
- Cache frequently accessed data (districts, colleges, courses)
- Use Django's cache framework for expensive operations

### 3. Static Files
- Use CDN for static files (optional)
- Enable gzip compression
- Optimize images and assets

---

## Emergency Procedures

### 1. Security Incident Response
1. Block suspicious IPs immediately
2. Review authentication logs
3. Check for data breaches
4. Rotate SECRET_KEY and other secrets
5. Notify affected users if needed

### 2. Database Recovery
1. Stop the web application
2. Restore from latest backup
3. Verify data integrity
4. Restart application
5. Monitor for issues

### 3. DDoS Response
1. Enable rate limiting
2. Block suspicious IP ranges
3. Consider using DDoS protection service
4. Monitor traffic patterns

---

## Contact and Support

For deployment issues:
- PythonAnywhere support: https://www.pythonanywhere.com/support/
- Django documentation: https://docs.djangoproject.com/
- DRF documentation: https://www.django-rest-framework.org/

---

## Post-Deployment Verification

### Test Endpoints

```bash
# Test public endpoint
curl https://oneteamprap.pythonanywhere.com/api/public/districts/

# Test student registration
curl -X POST https://oneteamprap.pythonanywhere.com/api/student/register/ \
  -H "Content-Type: application/json" \
  -d '{"studentName":"Test User","email":"test@example.com","mobile":"1234567890","district":"Test District","college":"Test College","course":"BCA"}'

# Test student login
curl -X POST https://oneteamprap.pythonanywhere.com/api/student/login/ \
  -H "Content-Type: application/json" \
  -d '{"mobile":"1234567890","password":"PRAP@7890"}'

# Test CORS from frontend
# Open browser console on your Vercel frontend and make API calls
```

### Security Verification

1. **Check security headers**:
   ```bash
   curl -I https://oneteamprap.pythonanywhere.com/api/public/districts/
   ```

2. **Verify SSL certificate**:
   - Visit https://oneteamprap.pythonanywhere.com
   - Check for valid SSL certificate

3. **Test rate limiting**:
   - Make multiple requests quickly
   - Verify 429 response after limit

4. **Test authentication**:
   - Try accessing admin endpoints without auth
   - Verify 401/403 responses

---

## Success Criteria

✅ Backend accessible at https://oneteamprap.pythonanywhere.com
✅ Frontend can successfully call API endpoints
✅ CORS properly configured for Vercel domain
✅ Security headers present in responses
✅ Rate limiting functional
✅ Email notifications working
✅ Database migrations applied
✅ Static files serving correctly
✅ SSL/HTTPS enabled
✅ No errors in logs
✅ Authentication and authorization working

---

## Next Steps

1. **Monitor** the application for the first 24-48 hours
2. **Review logs** for any security warnings or errors
3. **Test all functionality** from the frontend
4. **Set up monitoring alerts** for critical issues
5. **Document any custom configurations** for future reference
6. **Plan regular maintenance** and backup schedules