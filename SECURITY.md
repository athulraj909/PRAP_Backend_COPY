# API Security Documentation

## Overview
This document outlines the security measures implemented in the PRAP backend API to protect against unauthorized access, data breaches, and common web vulnerabilities.

## Security Issues Fixed

### 1. Exposed Secrets
- **Issue**: Email password was exposed in `.env.example`
- **Fix**: Removed actual credentials and replaced with placeholders
- **Action Required**: Generate new app-specific password for email service

### 2. Unauthenticated Access to Sensitive Data
- **Issue**: Public endpoints allowed unrestricted access to questions, student data, and exam results
- **Fix**: Implemented API key authentication for all public data endpoints
- **Action Required**: Configure API keys in environment variables

### 3. Rate Limiting Bypass
- **Issue**: GET requests were exempt from rate limiting, allowing abuse of public endpoints
- **Fix**: Removed GET exemption and implemented separate rate limits for public endpoints
- **Configuration**: Public routes use `RATE_LIMIT_PUBLIC_ENDPOINTS` (default: `1000/hour`).

### 4. Default Insecure Configuration
- **Issue**: Default SECRET_KEY and DEBUG=True in settings
- **Fix**: Made SECRET_KEY mandatory and changed DEBUG default to False
- **Action Required**: Set strong SECRET_KEY in production

### 5. Missing Input Validation
- **Issue**: Insufficient validation against SQL injection, XSS, and other attacks
- **Fix**: Enhanced request validation middleware with comprehensive pattern matching
- **Status**: Implemented in `api/middleware/request_validation.py`

## Security Features Implemented

### API Key Authentication
All public data endpoints now require API key authentication:
- `/public/questions/` - Exam questions
- `/public/districts/` - District data
- `/public/colleges/` - College data
- `/public/courses/` - Course data
- `/public/assessment-categories/` - Assessment categories
- `/public/exam-settings/` - Exam settings
- `/student/exam/submit/` - Exam submission
- `/student/exam/results/` - Student results

### Rate Limiting
Tiered rate limiting for different endpoint types:
- Anonymous users: 1000 requests/hour
- Authenticated users: 500 requests/hour
- Public endpoints: 1000 requests/hour
- DRF anonymous throttle: 1000 requests/hour (`API_ANON_THROTTLE_RATE`)
- Login endpoints: 1000 requests/hour per IP (`RATE_LIMIT_LOGIN` and `API_LOGIN_THROTTLE_RATE`)

### IP Security
- Automatic IP blocking after 5 failed login attempts
- Temporary IP blocks for suspicious activity
- Configurable IP whitelist/blacklist

### Security Headers
- Content Security Policy (CSP)
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy

### Input Validation
- SQL injection prevention
- XSS attack prevention
- Path traversal detection
- Command injection prevention
- Request size limits
- Content-Type validation

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Django Settings
SECRET_KEY=your-strong-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# API Key Authentication (comma-separated list)
VALID_API_KEYS=your-production-api-key,your-staging-api-key

# CORS Settings
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Rate Limiting
RATE_LIMIT_ANON=1000/hour
RATE_LIMIT_USER=500/hour
RATE_LIMIT_PUBLIC_ENDPOINTS=1000/hour
RATE_LIMIT_LOGIN=1000/hour
API_ANON_THROTTLE_RATE=1000/hour
API_LOGIN_THROTTLE_RATE=1000/hour

# IP Security
MAX_FAILED_ATTEMPTS=5
IP_BLOCK_DURATION=3600

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### Frontend Integration

Your frontend should include the API key in request headers:

```javascript
// Example using fetch
const API_KEY = 'your-api-key-here';

fetch('https://api.yourdomain.com/public/questions/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

```javascript
// Example using axios
import axios from 'axios';

const API_KEY = 'your-api-key-here';

axios.get('https://api.yourdomain.com/public/questions/', {
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => console.log(response.data));
```

## Workflow Explanation

### User Registration and Exam Flow

1. **Registration** (`/api/student/register/`)
   - Public endpoint (no API key required)
   - Users can register without authentication
   - Returns JWT token upon successful registration

2. **Login** (`/api/student/login/`)
   - Public endpoint (no API key required)
   - Users can login with mobile and password
   - Returns JWT token upon successful login

3. **Load Questions** (`/api/public/questions/`)
   - Requires API key authentication
   - Frontend sends API key in `X-API-Key` header
   - Returns active questions for exams

4. **Submit Exam** (`/api/student/exam/submit/`)
   - Requires API key authentication
   - Frontend sends API key in `X-API-Key` header
   - Submits exam results

5. **View Results** (`/api/student/exam/results/`)
   - Requires API key authentication
   - Frontend sends API key in `X-API-Key` header
   - Returns student's exam results

This flow ensures that:
- Legitimate users can register and login without barriers
- External tools cannot access your data without the API key
- Your frontend application has full access to all endpoints

## API Key Management

### Generating API Keys

Generate secure API keys using:

```python
import secrets
api_key = secrets.token_urlsafe(32)
print(api_key)
```

### Best Practices

1. **Use separate keys for different environments**
   - Development: `dev-key-xxxxx`
   - Staging: `staging-key-xxxxx`
   - Production: `prod-key-xxxxx`

2. **Rotate keys regularly**
   - Change API keys every 90 days
   - Maintain backward compatibility during transition

3. **Never commit API keys to version control**
   - Use environment variables
   - Use secret management services in production

4. **Monitor API key usage**
   - Track which keys are being used
   - Set up alerts for suspicious activity

## Deployment Checklist

### Before Production Deployment

- [ ] Set strong SECRET_KEY in environment variables
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS with your domain
- [ ] Set up SSL/TLS certificate
- [ ] Configure CORS_ALLOWED_ORIGINS with your frontend domain
- [ ] Generate and configure API keys
- [ ] Set SECURE_SSL_REDIRECT=True
- [ ] Set SESSION_COOKIE_SECURE=True
- [ ] Set CSRF_COOKIE_SECURE=True
- [ ] Configure email service with app-specific password
- [ ] Review and adjust rate limiting settings
- [ ] Configure database for production (PostgreSQL recommended)
- [ ] Set up proper logging and monitoring
- [ ] Configure backup strategy
- [ ] Test security headers using security headers scanner

### Security Testing

Test your API security using:

1. **Curl without API key** (should fail):
```bash
curl https://api.yourdomain.com/public/questions/
# Expected: 401 Unauthorized
```

2. **Curl with API key** (should succeed):
```bash
curl -H "X-API-Key: your-api-key" https://api.yourdomain.com/public/questions/
# Expected: 200 OK with questions data
```

3. **Rate limiting test** (should block after limit):
```bash
# Send 101 requests
for i in {1..101}; do curl https://api.yourdomain.com/public/questions/; done
# Expected: 429 Too Many Requests after 100 requests
```

## Monitoring and Maintenance

### Log Monitoring

Monitor these security events:
- Failed authentication attempts
- Rate limit violations
- Suspicious IP addresses
- Invalid API key attempts
- SQL injection/XSS attempts

### Regular Security Audits

- Review API key access logs monthly
- Check for unused API keys
- Review rate limiting effectiveness
- Audit failed login attempts
- Update security patterns as needed

## Contact

For security concerns or questions about this implementation, contact the development team.
