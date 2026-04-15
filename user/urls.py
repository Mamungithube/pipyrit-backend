from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterApiView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPApiView.as_view(), name='verify-otp'),
    path('login/', LoginAPIView.as_view(), name='login'),
]