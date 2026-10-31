"""
Rate Limiting Middleware
Implements rate limiting to prevent API abuse and DDoS attacks
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
import time
import logging
import hashlib

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Middleware to implement rate limiting based on IP address and user authentication
    """

    public_endpoint_prefixes = (
        '/public/',
        '/api/public/',
        '/student/exam/',
        '/api/student/exam/',
    )
    login_endpoint_paths = (
        '/student/login/',
        '/api/student/login/',
        '/admin/login/',
        '/api/admin/login/',
    )
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Get rate limits from settings or use defaults
        self.anon_limit = getattr(settings, 'RATE_LIMIT_ANON', '1000/hour')
        self.user_limit = getattr(settings, 'RATE_LIMIT_USER', '500/hour')
        self.public_limit = getattr(settings, 'RATE_LIMIT_PUBLIC_ENDPOINTS', '1000/hour')
        self.login_limit = getattr(settings, 'RATE_LIMIT_LOGIN', '1000/hour')
        
        # Parse rate limits (cached in __init__ to avoid repeated parsing)
        self.anon_requests, self.anon_period = self._parse_rate_limit(self.anon_limit)
        self.user_requests, self.user_period = self._parse_rate_limit(self.user_limit)
        self.public_requests, self.public_period = self._parse_rate_limit(self.public_limit)
        self.login_requests, self.login_period = self._parse_rate_limit(self.login_limit)
        
        # Cache for IP addresses to avoid repeated parsing
        self.ip_cache = {}
        
    def _parse_rate_limit(self, rate_string):
        """Parse rate limit string like '100/hour' into requests and period in seconds"""
        try:
            parts = rate_string.split('/')
            requests = int(parts[0])
            period_str = parts[1].lower()
            
            period_map = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }
            
            period = period_map.get(period_str, 3600)  # Default to hour
            return requests, period
        except (IndexError, ValueError):
            logger.warning(f"Invalid rate limit format: {rate_string}, using defaults")
            return 100, 3600
    
    def _get_client_ip(self, request):
        """Get client IP address considering proxy headers (optimized with caching)"""
        # Check cache first
        if hasattr(request, '_cached_client_ip'):
            return request._cached_client_ip
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Cache the result on the request object
        request._cached_client_ip = ip
        return ip
    
    def _get_rate_limit_key(self, request, ip, scope):
        """Generate cache key for rate limiting (optimized)"""
        if request.user.is_authenticated:
            key = f"rate_limit:{scope}:user_{request.user.id}"
        else:
            # Separate endpoint classes so one limit cannot consume another's quota.
            ip_hash = hashlib.md5(ip.encode()).hexdigest()[:12]  # Reduced from 16 to 12 chars
            key = f"rate_limit:{scope}:anon_{ip_hash}"
        return key

    def _is_public_endpoint(self, request):
        return request.path_info.startswith(self.public_endpoint_prefixes)

    def _get_rate_limit(self, request):
        if self._is_public_endpoint(request):
            return 'public', self.public_requests, self.public_period
        if request.path_info in self.login_endpoint_paths:
            return 'login', self.login_requests, self.login_period
        if request.user.is_authenticated:
            return 'user', self.user_requests, self.user_period
        return 'anon', self.anon_requests, self.anon_period

    def _has_bearer_token(self, request):
        authorization = request.META.get('HTTP_AUTHORIZATION', '')
        scheme, separator, token = authorization.partition(' ')
        return bool(separator and token and scheme.lower() == 'bearer')

    def _check_rate_limit(self, request, ip):
        """Check if request should be rate limited"""
        scope, limit, period = self._get_rate_limit(request)
        key = self._get_rate_limit_key(request, ip, scope)
        
        # Get current request count and timestamp
        data = cache.get(key)
        
        if data is None:
            # First request in window
            cache.set(key, {'count': 1, 'start_time': time.time()}, period)
            return True
        
        current_time = time.time()
        elapsed = current_time - data['start_time']
        
        # Reset if period has elapsed
        if elapsed >= period:
            cache.set(key, {'count': 1, 'start_time': current_time}, period)
            return True
        
        # Check if limit exceeded
        if data['count'] >= limit:
            logger.warning(f"Rate limit exceeded for {key}: {data['count']}/{limit}")
            return False
        
        # Increment counter
        data['count'] += 1
        cache.set(key, data, period)
        return True
    
    def __call__(self, request):
        # Skip rate limiting for static files and admin only
        # DO NOT skip for GET requests to prevent abuse of public endpoints
        if (request.path.startswith('/static/') or 
            request.path.startswith('/admin/')) or self._has_bearer_token(request):
            return self.get_response(request)

        ip = self._get_client_ip(request)
        scope, limit, period = self._get_rate_limit(request)
        key = self._get_rate_limit_key(request, ip, scope)
        
        # Check rate limit
        if not self._check_rate_limit(request, ip):
            response = JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': str(period)
            }, status=429)
            response['Retry-After'] = str(period)
            response['X-RateLimit-Limit'] = str(limit)
            response['X-RateLimit-Remaining'] = '0'
            return response
        
        response = self.get_response(request)
        
        # Add rate limit headers (simplified to reduce cache operations)
        try:
            response['X-RateLimit-Limit'] = str(limit)
            remaining = max(0, limit - cache.get(key, {}).get('count', 0))
            response['X-RateLimit-Remaining'] = str(remaining)
        except Exception:
            # Don't fail the request if header calculation fails
            pass
        
        return response