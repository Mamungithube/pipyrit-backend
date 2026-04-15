from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterApiView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPApiView.as_view(), name='verify-otp'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('forgot-password/verify/', ForgotPasswordVerifyOTPView.as_view(),
         name='forgot-password-verify'),
    path('forgot-password/set-password/',
         SetNewPasswordView.as_view(), name='set-new-password'),
]
