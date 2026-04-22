from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AppSubscriptionViewSet, 
    InAppPurchaseViewSet, 
    AdminSubscriptionPlanViewSet,
    AdminEarningDashboardViewSet
)

router = DefaultRouter()

# অ্যাপ এন্ডপয়েন্ট
router.register(r'plans', AppSubscriptionViewSet, basename='app-plans')
router.register(r'iap', InAppPurchaseViewSet, basename='iap-verify')
router.register(r'admin/earnings', AdminEarningDashboardViewSet, basename='admin-earnings')

# অ্যাডমিন এন্ডপয়েন্ট
router.register(r'admin/plans', AdminSubscriptionPlanViewSet, basename='admin-plans')

urlpatterns = [
    path('', include(router.urls)),
]