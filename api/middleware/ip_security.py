"""
IP Security Middleware
Implements IP-based security controls and access restrictions
"""

from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
import logging
import hashlib

logger = logging.getLogger(__name__)


class IPSecurityMiddleware:
    """
    Middleware to implement IP-based security controls
    - IP whitelist/blacklist
    - Suspicious activity detection
    - Geographic blocking (optional)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Security settings
        self.blocked_ips = getattr(settings, 'BLOCKED_IPS', [])
        self.allowed_ips = getattr(settings, 'ALLOWED_IPS', [])
        self.max_failed_attempts = getattr(settings, 'MAX_FAILED_ATTEMPTS', 5)
        self.block_duration = getattr(settings, 'IP_BLOCK_DURATION', 3600)  # 1 hour default
        
    def _get_client_ip(self, request):
        """Get client IP address considering proxy headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_ip_blocked(self, ip):
        """Check if IP is in blocked list or temporarily blocked due to suspicious activity"""
        # Check permanent block list
        if ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {ip}")
            return True
        
        # Check temporary block (due to failed attempts)
        block_key = f"ip_blocked:{ip}"
        if cache.get(block_key):
            logger.warning(f"Temporarily blocked IP attempted access: {ip}")
            return True
        
        return False
    
    def _is_ip_allowed(self, ip):
        """Check if IP is in allowed list (if whitelist is enabled)"""
        if self.allowed_ips:
            return ip in self.allowed_ips
        return True
    
    def _track_failed_attempt(self, request, ip):
        """Track failed authentication attempts"""
        if request.path in ['/api/student/login/', '/api/admin/login/']:
            fail_key = f"failed_attempts:{ip}"
            attempts = cache.get(fail_key, 0) + 1
            cache.set(fail_key, attempts, self.block_duration)
            
            # Block IP if too many failed attempts
            if attempts >= self.max_failed_attempts:
                block_key = f"ip_blocked:{ip}"
                cache.set(block_key, True, self.block_duration)
                logger.warning(f"IP blocked due to too many failed attempts: {ip}")
    
    def _detect_suspicious_activity(self, request, ip):
        """Detect suspicious patterns in requests"""
        suspicious_indicators = []
        
        # Check for SQL injection patterns
        sql_patterns = ['\' OR', '\' AND', 'UNION SELECT', 'DROP TABLE', '1=1']
        for param in request.GET.values():
            for pattern in sql_patterns:
                if pattern.lower() in str(param).lower():
                    suspicious_indicators.append('SQL injection pattern')
                    break
        
        # Check for XSS patterns
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
        for param in request.GET.values():
            for pattern in xss_patterns:
                if pattern.lower() in str(param).lower():
                    suspicious_indicators.append('XSS pattern')
                    break
        
        # Check for path traversal
        path_traversal = ['../', '..\\', '%2e%2e']
        for pattern in path_traversal:
            if pattern in request.path:
                suspicious_indicators.append('Path traversal')
                break
        
        if suspicious_indicators:
            logger.warning(f"Suspicious activity detected from {ip}: {suspicious_indicators}")
            # Temporarily block IPs with suspicious activity
            block_key = f"ip_blocked:{ip}"
            cache.set(block_key, True, self.block_duration)
            return True
        
        return False
    
    def _is_safe_request_method(self, request):
        """Check if request method is safe (GET, HEAD, OPTIONS)"""
        return request.method in ['GET', 'HEAD', 'OPTIONS']
    
    def __call__(self, request):
        ip = self._get_client_ip(request)
        
        # Skip IP checks for safe methods and static files
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Check if IP is blocked
        if self._is_ip_blocked(ip):
            return JsonResponse({
                'error': 'Access denied',
                'message': 'Your IP address has been blocked due to suspicious activity.'
            }, status=403)
        
        # Check if IP is allowed (if whitelist is enabled)
        if not self._is_ip_allowed(ip):
            logger.warning(f"IP not in whitelist: {ip}")
            return JsonResponse({
                'error': 'Access denied',
                'message': 'Your IP address is not authorized to access this resource.'
            }, status=403)
        
        # Detect suspicious activity
        if self._detect_suspicious_activity(request, ip):
            return JsonResponse({
                'error': 'Access denied',
                'message': 'Suspicious activity detected from your IP address.'
            }, status=403)
        
        response = self.get_response(request)
        
        # Track failed authentication attempts
        if response.status_code == 401:
            self._track_failed_attempt(request, ip)
        
        return response