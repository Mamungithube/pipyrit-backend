from django.db import router
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'admin/users', AdminUserManagementViewSet, basename='admin-users')
router.register(r'profile', UserProfileViewSet, basename='user-profile')
router.register(r'admin/profile', AdminProfileViewSet, basename='admin-profile')
router.register(r'admin/dashboard-home', AdminDashboardHomeViewSet, basename='admin-dashboard-home')

urlpatterns = [
    path('register/', RegisterApiView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPApiView.as_view(), name='verify-otp'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('forgot-password/verify/', ForgotPasswordVerifyOTPView.as_view(),
         name='forgot-password-verify'),
    path('forgot-password/set-password/',
         SetNewPasswordView.as_view(), name='set-new-password'),
     
     path('', include(router.urls)),
         
]
