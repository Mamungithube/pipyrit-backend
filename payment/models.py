from django.db import models
from django.conf import settings

# ১. সাবস্ক্রিপশন প্ল্যান (অ্যাডমিন এটি তৈরি করবে - Image 13)
class SubscriptionPlan(models.Model):
    PLAN_TYPE = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    name = models.CharField(max_length=100) # যেমন: Premium Yearly Plan
    price = models.DecimalField(max_digits=10, decimal_places=2) # যেমন: 19.99
    billing_cycle = models.CharField(max_length=20, choices=PLAN_TYPE)
    description = models.TextField(blank=True, null=True)
    features = models.JSONField(help_text="List of features") # যেমন: ['Access all quiz', 'Voice mode']
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

# ২. ইউজারের বর্তমান সাবস্ক্রিপশন স্ট্যাটাস
class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)

    platform = models.CharField(max_length=20) # ios, android
    store_transaction_id = models.CharField(max_length=255, unique=True)
    
    start_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    
    is_trial_used = models.BooleanField(default=False) # ৭ দিনের ট্রায়াল একবারই পাবে
    is_active = models.BooleanField(default=False) # পেমেন্ট সাকসেস হলে True হবে

    def __str__(self):
        return f"{self.user.email} - {self.plan.name if self.plan else 'No Plan'}"

# ৩. ট্রানজ্যাকশন হিস্ট্রি (অ্যাডমিন ড্যাশবোর্ডের গ্রাফের জন্য - Image 12)
class Transaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    
    invoice_id = models.CharField(max_length=100, unique=True) # যেমন: INV-12345
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, blank=True, null=True) # Stripe/PayPal ID
    payment_method = models.CharField(max_length=50) # Credit Card, PayPal, Apple Pay
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_id