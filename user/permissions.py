from rest_framework import permissions
from django.utils import timezone

class IsPremiumUser(permissions.BasePermission):
    """
    Users will only get access if they are an active subscriber or are in a trial period.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        subscription = getattr(request.user, 'subscription', None)
        if subscription and subscription.is_active and subscription.expiry_date > timezone.now():
            return True
        return False