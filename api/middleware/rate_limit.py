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
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Get rate limits from settings or use defaults
        self.anon_limit = getattr(settings, 'RATE_LIMIT_ANON', '100/hour')
        self.user_limit = getattr(settings, 'RATE_LIMIT_USER', '1000/hour')
        
        # Parse rate limits
        self.anon_requests, self.anon_period = self._parse_rate_limit(self.anon_limit)
        self.user_requests, self.user_period = self._parse_rate_limit(self.user_limit)
        
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
        """Get client IP address considering proxy headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_rate_limit_key(self, request, ip):
        """Generate cache key for rate limiting"""
        if request.user.is_authenticated:
            # Use user ID for authenticated users
            key = f"rate_limit:user_{request.user.id}"
        else:
            # Use IP address for anonymous users
            ip_hash = hashlib.md5(ip.encode()).hexdigest()[:16]
            key = f"rate_limit:anon_{ip_hash}"
        return key
    
    def _check_rate_limit(self, request, ip):
        """Check if request should be rate limited"""
        key = self._get_rate_limit_key(request, ip)
        
        # Get current request count and timestamp
        data = cache.get(key)
        
        if data is None:
            # First request in window
            cache.set(key, {'count': 1, 'start_time': time.time()}, self.anon_period if not request.user.is_authenticated else self.user_period)
            return True
        
        current_time = time.time()
        elapsed = current_time - data['start_time']
        
        # Determine appropriate limit based on authentication
        if request.user.is_authenticated:
            limit = self.user_requests
            period = self.user_period
        else:
            limit = self.anon_requests
            period = self.anon_period
        
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
        # Skip rate limiting for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        
        ip = self._get_client_ip(request)
        
        # Check rate limit
        if not self._check_rate_limit(request, ip):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': self.anon_period if not request.user.is_authenticated else self.user_period
            }, status=429)
        
        response = self.get_response(request)
        
        # Add rate limit headers
        if request.user.is_authenticated:
            response['X-RateLimit-Limit'] = str(self.user_requests)
            response['X-RateLimit-Remaining'] = str(max(0, self.user_requests - cache.get(self._get_rate_limit_key(request, ip), {}).get('count', 0)))
        else:
            response['X-RateLimit-Limit'] = str(self.anon_requests)
            response['X-RateLimit-Remaining'] = str(max(0, self.anon_requests - cache.get(self._get_rate_limit_key(request, ip), {}).get('count', 0)))
        
        return response