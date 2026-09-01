"""
Request Validation Middleware
Validates incoming requests for security compliance
"""

from django.http import JsonResponse
from django.conf import settings
import logging
import re

logger = logging.getLogger(__name__)


class RequestValidationMiddleware:
    """
    Middleware to validate incoming requests for security compliance
    - User-Agent validation
    - Content-Type validation
    - Request size limits
    - Header validation
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Validation settings
        self.max_request_size = getattr(settings, 'MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB default
        self.require_user_agent = getattr(settings, 'REQUIRE_USER_AGENT', True)
        self.allowed_content_types = set(getattr(settings, 'ALLOWED_CONTENT_TYPES', [
            'application/json',
            'multipart/form-data',
            'application/x-www-form-urlencoded'
        ]))
        
        # Pre-compile regex patterns for better performance
        self.blocked_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python-requests', 'libwww-perl']
        ]
        
    def _has_valid_user_agent(self, request):
        """Check if request has a valid User-Agent header (optimized)"""
        if not self.require_user_agent:
            return True
            
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Block empty user agents
        if not user_agent or user_agent.strip() == '':
            logger.warning("Request blocked: No User-Agent header")
            return False
        
        # Block suspicious user agents (skip for public endpoints to reduce CPU)
        if request.path.startswith('/api/public/') or request.path == '/api/health/':
            return True
        
        user_agent_lower = user_agent.lower()
        for pattern in self.blocked_patterns:
            if pattern.search(user_agent_lower):
                logger.warning(f"Request blocked: Suspicious User-Agent: {user_agent}")
                return False
        
        return True
    
    def _has_valid_content_type(self, request):
        """Check if request has valid Content-Type for POST/PUT/PATCH (optimized)"""
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return True
            
        content_type = request.META.get('CONTENT_TYPE', '').split(';')[0].strip()
        
        # Allow requests without content type for file uploads
        if request.path.startswith('/api/questions/batch/'):
            return True
        
        if not content_type:
            logger.warning(f"Request blocked: No Content-Type for {request.method} request")
            return False
        
        # Use set for O(1) lookup instead of list
        if content_type not in self.allowed_content_types:
            logger.warning(f"Request blocked: Invalid Content-Type: {content_type}")
            return False
        
        return True
    
    def _check_request_size(self, request):
        """Check if request size is within limits"""
        if request.method == 'GET':
            return True
            
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(f"Request blocked: Size {size} exceeds limit {self.max_request_size}")
                    return False
            except ValueError:
                pass
        
        return True
    
    def _validate_headers(self, request):
        """Validate request headers for security"""
        # Check for suspicious headers
        suspicious_headers = [
            'X-Forwarded-Host',
            'X-Original-Host',
            'X-Real-IP'
        ]
        
        for header in suspicious_headers:
            if header in request.META:
                # Log but don't block - these are common in legitimate setups
                logger.debug(f"Suspicious header detected: {header}")
        
        return True
    
    def _check_referer_origin(self, request):
        """Validate Referer header for POST requests (optimized)"""
        if request.method != 'POST':
            return True
            
        referer = request.META.get('HTTP_REFERER', '')
        if not referer:
            return True  # Allow requests without referer
        
        # Quick check for known good origins
        if 'vercel.app' in referer or 'localhost' in referer or '127.0.0.1' in referer:
            return True
        
        # Check if referer is from allowed origins
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if isinstance(allowed_origins, str):
            allowed_origins = [origin.strip() for origin in allowed_origins.split(',')]
        
        for origin in allowed_origins:
            if origin in referer:
                return True
        
        logger.warning(f"Request blocked: Invalid Referer: {referer}")
        return False
    
    def __call__(self, request):
        # Skip validation for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Skip health check endpoints
        if request.path in ['/health/', '/api/health/']:
            return self.get_response(request)
        
        # Validate User-Agent
        if not self._has_valid_user_agent(request):
            return JsonResponse({
                'error': 'Invalid request',
                'message': 'Invalid User-Agent header'
            }, status=400)
        
        # Validate Content-Type
        if not self._has_valid_content_type(request):
            return JsonResponse({
                'error': 'Invalid request',
                'message': 'Invalid Content-Type header'
            }, status=400)
        
        # Check request size
        if not self._check_request_size(request):
            return JsonResponse({
                'error': 'Request too large',
                'message': f'Request size exceeds maximum allowed size of {self.max_request_size} bytes'
            }, status=413)
        
        # Validate headers
        if not self._validate_headers(request):
            return JsonResponse({
                'error': 'Invalid request',
                'message': 'Invalid request headers'
            }, status=400)
        
        # Check referer origin
        if not self._check_referer_origin(request):
            return JsonResponse({
                'error': 'Invalid request',
                'message': 'Invalid Referer header'
            }, status=400)
        
        return self.get_response(request)