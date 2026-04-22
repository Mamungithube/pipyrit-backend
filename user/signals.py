from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


from django.utils import timezone
from datetime import timedelta
from payment.models import UserSubscription

@receiver(post_save, sender=User)
def start_free_trial(sender, instance, created, **kwargs):
    if created:
        # রেজিস্ট্রেশনের সময় ৭ দিনের ট্রায়াল সেট করা
        expiry = timezone.now() + timedelta(days=7)
        UserSubscription.objects.create(
            user=instance, 
            expiry_date=expiry, 
            is_active=True, # ট্রায়াল পিরিয়ডে একটিভ থাকবে
            is_trial_used=True
        )