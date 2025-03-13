from typing import Optional
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth.backends import BaseBackend

User = get_user_model()

def otp_cache_key(email: str) -> str:
    """Generate a cache key for OTP storage."""
    return f"email_otp_{email.lower()}"

class OTPBackend(BaseBackend):
    """Authentication backend for OTP-based login."""
    
    def authenticate(self, request, email: Optional[str] = None, code: Optional[str] = None) -> Optional[User]:
        """Authenticate a user with email and OTP code."""
        if not (email and code):
            return None
            
        try:
            validate_email(email)
        except ValidationError:
            return None
        cache_key = otp_cache_key(email)
        
        cached_data = cache.get(cache_key)
        if not cached_data or cached_data['code'] != code:
            return None
            
        cache.delete(cache_key)
        user, _ = User.objects.get_or_create(email=email.lower())
        return user

    def get_user(self, user_id) -> Optional[User]:
        """Retrieve user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None