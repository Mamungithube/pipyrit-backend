from rest_framework import permissions
from django.utils import timezone

class IsPremiumUser(permissions.BasePermission):
    """
    ইউজার যদি একটিভ সাবস্ক্রাইবার হয় অথবা ট্রায়াল পিরিয়ডে থাকে তবেই এক্সেস পাবে।
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        subscription = getattr(request.user, 'subscription', None)
        if subscription and subscription.is_active and subscription.expiry_date > timezone.now():
            return True
        return False