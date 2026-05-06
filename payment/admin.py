from django.contrib import admin

# Register your models here.

from .models import SubscriptionPlan, UserSubscription, Transaction
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'billing_cycle', 'is_active')
    list_filter = ('billing_cycle', 'is_active')
    search_fields = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'platform', 'store_transaction_id', 'start_date', 'expiry_date', 'is_active')
    list_filter = ('platform', 'is_active')
    search_fields = ('user__email', 'plan__name')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'user', 'plan', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('invoice_id', 'user__email', 'plan__name')