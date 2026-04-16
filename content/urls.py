from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppSiteSettingView, AdminSiteSettingViewSet

router = DefaultRouter()
router.register(r'admin/settings', AdminSiteSettingViewSet, basename='admin-settings')

urlpatterns = [
    # ইউজারের জন্য এন্ডপয়েন্ট: /api/system/legal/privacy_policy/
    path('legal/<str:key>/', AppSiteSettingView.as_view(), name='app-legal-content'),
    
    path('', include(router.urls)),
]