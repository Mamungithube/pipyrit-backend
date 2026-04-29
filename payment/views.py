from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .models import SubscriptionPlan, UserSubscription, Transaction
from .serializers import AdminEarningTableSerializer, SubscriptionPlanSerializer, TransactionSerializer
from user.views import api_response, CustomPagination
from django.shortcuts import get_object_or_404

# --- 1. App API (User Section) ---

class AppSubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """User can only view active plans."""
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['8. Payment - App'])
    def list(self, request, *args, **kwargs):
        return api_response(True, "Plans fetched", self.get_serializer(self.get_queryset(), many=True).data)

    @swagger_auto_schema(tags=['8. Payment - App'])
    def retrieve(self, request, *args, **kwargs):
        return api_response(True, "Plan details fetched", self.get_serializer(self.get_object()).data)


class InAppPurchaseViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['8. Payment - App'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'platform': openapi.Schema(type=openapi.TYPE_STRING, description="ios/android"),
                'plan_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'purchase_token': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['platform', 'plan_id', 'purchase_token']
        )
    )
    @action(detail=False, methods=['post'], url_path='verify-purchase')
    def verify_purchase(self, request):
        user = request.user
        plan_id = request.data.get('plan_id')
        platform = request.data.get('platform')
        token = request.data.get('purchase_token')

        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        
        # Subscription update logic
        sub, _ = UserSubscription.objects.get_or_create(user=user)
        sub.plan = plan
        sub.platform = platform
        sub.store_transaction_id = token # Real purchase ID will be here
        sub.is_active = True
        
        days = 30 if plan.billing_cycle == 'monthly' else 365
        sub.expiry_date = timezone.now() + timedelta(days=days)
        sub.save()

        # Save Transaction (for Earnings Dashboard)
        Transaction.objects.create(
            user=user, plan=plan, invoice_id=f"IAP-{int(timezone.now().timestamp())}",
            amount=plan.price, payment_method=platform, status='completed'
        )

        return api_response(True, "Subscription activated successfully", {"expiry_date": sub.expiry_date})


# --- 2. Admin APIs (Admin Dashboard Section) ---

class AdminSubscriptionPlanViewSet(viewsets.ModelViewSet):
    """Admin dashboard for managing plans (Image 13)"""
    queryset = SubscriptionPlan.objects.all().order_by('-id')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Admin - Payment Management'])
    def list(self, request, *args, **kwargs):
        return api_response(True, "All plans fetched", self.get_serializer(self.get_queryset(), many=True).data)

    @swagger_auto_schema(tags=['Admin - Payment Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Plan created", serializer.data, status.HTTP_201_CREATED)
        return api_response(False, "Failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - Payment Management'])
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Plan updated", serializer.data)
        return api_response(False, "Update failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - Payment Management'])
    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return api_response(True, "Plan deleted", None, status.HTTP_204_NO_CONTENT)


class AdminEarningDashboardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all().order_by('-created_at')
    serializer_class = AdminEarningTableSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['invoice_id', 'user__full_name', 'transaction_id']  

    @swagger_auto_schema(tags=['Admin - Payment Management'])
    def list(self, request, *args, **kwargs):
        # 1. Weekly Revenue Calculation (Last 7 Days)
        last_week = timezone.now() - timedelta(days=7)
        weekly_revenue = Transaction.objects.filter(
            status='completed', 
            created_at__gte=last_week
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # 2. Table Data (With Pagination)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Custom paginated response
            response = self.get_paginated_response(serializer.data)
            # Insert Weekly Revenue into the response
            response.data['weekly_revenue'] = float(weekly_revenue)
            return response

        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Earnings fetched", {
            "weekly_revenue": float(weekly_revenue),
            "results": serializer.data
        })