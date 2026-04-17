import time
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

from .models import User, Profile
from .serializers import RegistrationSerializer, LoginSerializer, VerifyOTPSerializer, UserSerializer, ForgotPasswordSerializer, ForgotPasswordVerifySerializer, SetNewPasswordSerializer, ProfileSerializer, ChangePasswordSerializer
from .utils import generate_otp
from drf_yasg.utils import swagger_auto_schema

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from .serializers import AdminUserManagementSerializer


def api_response(success, message, data=None, status_code=status.HTTP_200_OK):
    """
    Standardized API response format for all endpoints.
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

    @swagger_auto_schema(tags=['1. Authentication'])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_msg = list(serializer.errors.values())[0][0]
            return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            profile, created = Profile.objects.get_or_create(user=user)

            otp_code = generate_otp()
            profile.otp = otp_code
            profile.otp_created_at = timezone.now()
            profile.save()

            # email sending logic
            try:
                msg = EmailMessage(
                    'Verify your email - Pipyrit',
                    f'Your verification code is: {otp_code}. It will expire in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email]
                )
                msg.send()
            except Exception as e:
                return api_response(True, "Registration success, but failed to send email. Please resend OTP.", {"email": user.email}, status.HTTP_201_CREATED)

            return api_response(True, "Verification code sent to your email.", {"email": user.email}, status.HTTP_201_CREATED)

        except Exception as e:
            return api_response(False, "Internal server error during registration.", {"detail": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

# Verify OTP View

class VerifyOTPApiView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['1. Authentication'])
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

        if not profile.otp:
            return api_response(False, "No active OTP found. Please request a new one.", None, status.HTTP_400_BAD_REQUEST)

        expiry_time = profile.otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return api_response(False, "OTP has expired. Please resend a new code.", None, status.HTTP_400_BAD_REQUEST)

        if profile.otp == otp:
            user.is_active = True
            user.save()
            profile.is_verified = True
            profile.otp = None  
            profile.save()
            return api_response(True, "Your account has been verified successfully.")

        return api_response(False, "Invalid verification code. Please try again.", None, status.HTTP_400_BAD_REQUEST)

# Login View

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['1. Authentication'])
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

# 1. Forgot Password - Request OTP
class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['2. Authentication'])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_msg = list(serializer.errors.values())[0][0]
            return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            return api_response(False, "No account found with this email.", None, status.HTTP_404_NOT_FOUND)

        otp_code = generate_otp()
        profile = user.profile
        profile.otp = otp_code
        profile.otp_created_at = timezone.now()
        profile.save()

        try:
            msg = EmailMessage(
                'Reset your password - Pipyrit',
                f'Your password reset code is: {otp_code}. Valid for 5 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            msg.send()
        except Exception:
            return api_response(False, "Failed to send email. Try again.", None, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return api_response(True, "Password reset code sent to your email.", {"email": email})

# 2. Verify OTP for Password Reset

class ForgotPasswordVerifyOTPView(generics.GenericAPIView):
    serializer_class = ForgotPasswordVerifySerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['2. Authentication'])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid data", serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        user = User.objects.filter(email=email).first()

        if not user or user.profile.otp != otp:
            return api_response(False, "Invalid or expired OTP.", None, status.HTTP_400_BAD_REQUEST)

        expiry_time = user.profile.otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return api_response(False, "OTP has expired.", None, status.HTTP_400_BAD_REQUEST)

        return api_response(True, "OTP verified. You can now reset your password.")

# 3. Set New Password

class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['2. Authentication'])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_msg = list(serializer.errors.values())[0][0]
            if isinstance(error_msg, list):
                error_msg = error_msg[0]
            return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['password']

        user = User.objects.filter(email=email).first()
        if not user or user.profile.otp != otp:
            return api_response(False, "Request unauthorized or OTP invalid.", None, status.HTTP_401_UNAUTHORIZED)

        user.set_password(new_password)
        user.save()

        user.profile.otp = None
        user.profile.save()

        return api_response(True, "Password has been reset successfully. You can now login.")


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = AdminUserManagementSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'email'] 

    @swagger_auto_schema(tags=['Admin - User Management'])
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "User list fetched", serializer.data)

    @swagger_auto_schema(tags=['Admin - User Management'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - User Management'])
    @action(detail=True, methods=['patch'], url_path='toggle-block')
    def toggle_block(self, request, pk=None):

        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        status_msg = "Blocked" if not user.is_active else "Unblocked"
        return api_response(True, f"User has been {status_msg}", None)

    @swagger_auto_schema(tags=['Admin - User Management'])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class UserProfileViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Profile.objects.none()
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        profile, created = Profile.objects.get_or_create(
            user=self.request.user)
        return profile

    @swagger_auto_schema(tags=['6. User Profile & Settings - App'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['full_name'] = request.user.full_name
        data['email'] = request.user.email
        return api_response(True, "Profile fetched", data)

    @swagger_auto_schema(tags=['6. User Profile & Settings - App'])
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Profile updated successfully", serializer.data)
        return api_response(False, "Update failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

        error_msg = list(serializer.errors.values())[0][0]
        return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['6. User Profile & Settings - App'], request_body=ChangePasswordSerializer)
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data.get("old_password")):
                return api_response(False, "Current password is wrong", None, status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data.get("new_password"))
            user.save()
            return api_response(True, "Password updated successfully", None)
        return api_response(False, "Validation Error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['6. User Profile & Settings - App'])
    @action(detail=False, methods=['delete'], url_path='delete-account')
    def delete_account(self, request):
        request.user.delete()
        return api_response(True, "Account deleted successfully", None)

# --- ADMIN PROFILE VIEWSET ---


class AdminProfileViewSet(UserProfileViewSet):
    queryset = Profile.objects.all() 

    @swagger_auto_schema(tags=['Admin - User Management'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - User Management'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class AdminDashboardStatsView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Admin - Dashboard'])
    def get(self, request):
        total_user = User.objects.filter(is_staff=False).count()
        registration_stats = User.objects.filter(is_staff=False).annotate(
            month=ExtractMonth('date_joined')
        ).values('month').annotate(count=Count('id')).order_by('month')

        data = {
            "total_users": total_user,
            "new_registrations": User.objects.filter(date_joined__date=timezone.now().date()).count(),
            "total_revenue": 0,  
            "chart_data": list(registration_stats)
        }
        return api_response(True, "Dashboard stats fetched", data)
