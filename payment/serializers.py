from rest_framework import serializers
from .models import SubscriptionPlan, Transaction

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'price', 'billing_cycle', 'description', 'features', 'is_active']

class TransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'invoice_id', 'user_email', 'plan_name', 'amount', 'payment_method', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class AdminEarningTableSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_image = serializers.ImageField(source='user.profile.profile_picture', read_only=True)
    subscription_name = serializers.CharField(source='plan.name', read_only=True)
    date = serializers.DateTimeField(source='created_at', format="%b, %d %Y %I:%M %p", read_only=True)

    class Meta:
        model = Transaction
        # এখান থেকে 'account_number' সরিয়ে ফেলা হয়েছে
        # তার বদলে আপনার মডেলে থাকা 'transaction_id' রাখা হয়েছে
        fields = [
            'id', 'invoice_id', 'user_name', 'user_image', 
            'subscription_name', 'amount', 'transaction_id', 'date', 'status'
        ]