import time
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

from .models import User, Profile
from .serializers import RegistrationSerializer, LoginSerializer, VerifyOTPSerializer, UserSerializer
from .utils import generate_otp

def api_response(success, message, data=None, status_code=status.HTTP_200_OK):
    """
    একই ফরম্যাটে রেসপন্স পাঠানোর জন্য গ্লোবাল হেল্পার ফাংশন।
    """
    return Response({
        "code": status_code,
        "success": success,
        "message": message,
        "timestamp": int(time.time()),
        "data": data
    }, status=status_code)

# Register View
class RegisterApiView(generics.GenericAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # প্রথম এরর মেসেজটি খুঁজে বের করা প্রফেশনাল ইউআই-এর জন্য
            error_msg = list(serializer.errors.values())[0][0]
            return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            profile, created = Profile.objects.get_or_create(user=user)
            
            otp_code = generate_otp()
            profile.otp = otp_code
            profile.otp_created_at = timezone.now()
            profile.save()
            
            # ইমেইল লজিক
            try:
                msg = EmailMessage(
                    'Verify your email - Pipyrit',
                    f'Your verification code is: {otp_code}. It will expire in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email]
                )
                msg.send()
            except Exception as e:
                # ইমেইল না গেলেও যেন ইউজারকে জানানো হয় সিস্টেমের সমস্যা
                return api_response(True, "Registration success, but failed to send email. Please resend OTP.", {"email": user.email}, status.HTTP_201_CREATED)
            
            return api_response(True, "Verification code sent to your email.", {"email": user.email}, status.HTTP_201_CREATED)
            
        except Exception as e:
            return api_response(False, "Internal server error during registration.", {"detail": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP View
class VerifyOTPApiView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_msg = list(serializer.errors.values())[0][0]
            return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        user = User.objects.filter(email=email).first()
        if not user:
            return api_response(False, "No account found with this email.", None, status.HTTP_404_NOT_FOUND)
        
        profile = user.profile
        
        # ওটিপি চেক করার আগে চেক করা যে ওটিপি আদৌ জেনারেট হয়েছে কি না
        if not profile.otp:
            return api_response(False, "No active OTP found. Please request a new one.", None, status.HTTP_400_BAD_REQUEST)

        # ওটিপি এক্সপায়ারি চেক (৫ মিনিটের লজিক)
        expiry_time = profile.otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return api_response(False, "OTP has expired. Please resend a new code.", None, status.HTTP_400_BAD_REQUEST)

        # ওটিপি ভেরিফিকেশন
        if profile.otp == otp:
            user.is_active = True
            user.save()
            profile.is_verified = True
            profile.otp = None # ভেরিফাই হয়ে গেলে ওটিপি ক্লিয়ার করে দেওয়া সিকিউর
            profile.save()
            return api_response(True, "Your account has been verified successfully.")
        
        return api_response(False, "Invalid verification code. Please try again.", None, status.HTTP_400_BAD_REQUEST)

# Login View
class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_msg = list(serializer.errors.values())[0][0]
            return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = User.objects.filter(email=email).first()
        
        if not user:
            return api_response(False, "No account exists with this email.", None, status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return api_response(False, "Incorrect password. Please try again.", None, status.HTTP_401_UNAUTHORIZED)
            
        if not user.is_active:
            return api_response(False, "Your email is not verified. Please verify your OTP first.", {"is_verified": False}, status.HTTP_403_FORBIDDEN)
        
        try:
            refresh = RefreshToken.for_user(user)
            data = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data
            }
            return api_response(True, "Logged in successfully.", data)
        except Exception as e:
            return api_response(False, "Failed to generate tokens.", {"detail": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)