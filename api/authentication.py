"""
API Key Authentication
Provides API key-based authentication for public endpoints
"""

from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key authentication for public endpoints
    Clients must provide a valid API key in the X-API-Key header
    """
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return None  # No API key provided, let other auth methods handle it
        
        # Get valid API keys from settings
        valid_api_keys = getattr(settings, 'VALID_API_KEYS', [])
        
        if not valid_api_keys:
            logger.warning("API key authentication enabled but no valid keys configured")
            raise exceptions.AuthenticationFailed('API key authentication not properly configured')
        
        if api_key not in valid_api_keys:
            logger.warning(f"Invalid API key attempt from IP: {self._get_client_ip(request)}")
            raise exceptions.AuthenticationFailed('Invalid API key')
        
        # Return a dummy user for API key authentication
        class APIKeyUser:
            is_authenticated = True
            is_anonymous = False
        
        return (APIKeyUser(), None)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
