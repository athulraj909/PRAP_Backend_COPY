"""
Security Headers Middleware
Adds comprehensive security headers to all HTTP responses
"""

from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    Implements OWASP security best practices
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add headers in production
        if not settings.DEBUG:
            # Content Security Policy (CSP)
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self' https://oneteamprap.pythonanywhere.com https://prapfrontendhosted.vercel.app",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response['Content-Security-Policy'] = '; '.join(csp_directives)
            
            # Strict-Transport-Security (HSTS)
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # X-Content-Type-Options
            response['X-Content-Type-Options'] = 'nosniff'
            
            # X-Frame-Options
            response['X-Frame-Options'] = 'DENY'
            
            # X-XSS-Protection
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Referrer-Policy
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy
            permissions_directives = [
                "geolocation=()",
                "microphone=()",
                "camera=()",
                "payment=()",
            ]
            response['Permissions-Policy'] = ', '.join(permissions_directives)
            
            # Remove server information
            response.pop('Server', None)
            
        return response