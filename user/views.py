import email
import time
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

from payment.models import Transaction

from .models import User, Profile
from .serializers import RegistrationSerializer, LoginSerializer, VerifyOTPSerializer, UserSerializer, ForgotPasswordSerializer, ForgotPasswordVerifySerializer, SetNewPasswordSerializer, ProfileSerializer, ChangePasswordSerializer
from .utils import generate_otp
from drf_yasg.utils import swagger_auto_schema

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from .serializers import AdminUserManagementSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Notification, DeviceToken
from .serializers import NotificationSerializer, DeviceTokenSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import time
import math


class CustomPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        total_count = self.page.paginator.count
        page_size = self.get_page_size(self.request)
        total_pages = math.ceil(total_count / page_size) if page_size else 1

        return Response({
            "code": 200,
            "success": True,
            "message": "Data fetched successfully",
            "timestamp": int(time.time()),
            "pagination": {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": self.page.number,
                "page_size": page_size,
                "has_next": self.page.has_next(),
                "has_previous": self.page.has_previous(),
                "next_page": self.page.next_page_number() if self.page.has_next() else None,
                "prev_page": self.page.previous_page_number() if self.page.has_previous() else None,
            },
            "results": data
        })


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
            user.is_active = False
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)
            otp_code = generate_otp()
            profile.otp = otp_code
            profile.otp_created_at = timezone.now()
            profile.save()

            try:
                msg = EmailMessage(
                    'Verify your email - Pipyrit',
                    f'Your verification code is: {otp_code}. It will expire in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email]
                )
                msg.send()
            except Exception:
                return api_response(True, "Registration success, but failed to send email. Please resend OTP.", {"email": user.email}, status.HTTP_201_CREATED)

            return api_response(True, "Verification code sent to your email.", {"email": user.email}, status.HTTP_201_CREATED)

        except Exception as e:
            return api_response(False, "Internal server error.", {"detail": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return api_response(False, "No account found.", None, status.HTTP_404_NOT_FOUND)

        profile = user.profile
        expiry_time = profile.otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return api_response(False, "OTP has expired.", None, status.HTTP_400_BAD_REQUEST)

        if profile.otp == otp:
            User.objects.filter(id=user.id).update(is_active=True)

            profile.is_verified = True
            profile.otp = None
            profile.save()

            user.refresh_from_db()

            refresh = RefreshToken.for_user(user)
            data = {"accessToken": str(refresh.access_token)}
            return api_response(True, "Otp verified successfully", data)

        return api_response(False, "Invalid verification code.", None, status.HTTP_400_BAD_REQUEST)


# Login View

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

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
                "user": UserSerializer(user, context={'request': request}).data
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
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.otp = otp_code
        profile.otp_created_at = timezone.now()
        profile.save()

        expires_at = (profile.otp_created_at +
                      timedelta(minutes=5)).isoformat()

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

        data = {
            "email": email,
            "otp": otp_code,
            "expiresAt": expires_at
        }
        return api_response(True, f"OTP sent to your email:{email}", data)

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

        refresh = RefreshToken.for_user(user)
        data = {
            "accessToken": str(refresh.access_token)
        }
        return api_response(True, "Otp verified successfully", data)


# 3. Set New Password (Authenticated via accessToken from previous step)
class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    # permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['2. Authentication'])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_msg = list(serializer.errors.values())[0][0]
            return api_response(False, error_msg, serializer.errors, status.HTTP_400_BAD_REQUEST)

        # Automatic user can be obtained from token
        user = request.user
        new_password = serializer.validated_data.get('confirm_password')

        # password update
        user.set_password(new_password)
        user.save()

        # Clearing OTP after password change (for security)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.otp = None
        profile.save()

        # Generate new token (to keep logged in)
        refresh = RefreshToken.for_user(user)
        data = {
            "accessToken": str(refresh.access_token),
            "refreshToken": str(refresh)
        }

        return api_response(True, "Password changed successfully.", data)


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = AdminUserManagementSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'email']
    pagination_class = CustomPagination

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
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "User details fetched", serializer.data)

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
        instance = self.get_object()
        instance.delete()
        return api_response(True, "User deleted successfully", None, status.HTTP_204_NO_CONTENT)


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

        full_name = request.data.get('full_name')
        if full_name:
            instance.user.full_name = full_name
            instance.user.save()

        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            data['full_name'] = instance.user.full_name
            data['email'] = instance.user.email
            return api_response(True, "Profile updated successfully", data)
        return api_response(False, "Update failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

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


class AdminDashboardHomeViewSet(viewsets.GenericViewSet):
    """
    A single API endpoint that provides status cards, 12-month charts, and paginated user lists.
    """
    permission_classes = [IsAdminUser]
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = AdminUserManagementSerializer
    pagination_class = CustomPagination

    @swagger_auto_schema(tags=['Admin - Dashboard'])
    def list(self, request, *args, **kwargs):
        # --- 1. Top Cards and Status Calculation ---
        total_user = User.objects.filter(is_staff=False).count()

        # New Registrations for the Current Month
        current_month = timezone.now().month
        new_registrations = User.objects.filter(
            is_staff=False,
            date_joined__month=current_month
        ).count()

        # Total Revenue
        total_revenue = Transaction.objects.filter(
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # --- 2. Earning Summary Chart Data (12 Months of Data) ---
        # Fetch only the months that have income
        chart_stats = Transaction.objects.filter(
            status='completed'
        ).annotate(
            month=ExtractMonth('created_at')
        ).values('month').annotate(total=Sum('amount')).order_by('month')

        # Convert QuerySet to Dictionary (for easy matching)
        stats_dict = {item['month']: item['total'] for item in chart_stats}

        # 12 Months List (According to Figma Jan-Dec)
        full_year_chart = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May',
                       'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        for i in range(1, 13):
            full_year_chart.append({
                "month_index": i,
                "month_name": month_names[i-1],
                "total": float(stats_dict.get(i, 0))  # If no income, then 0.0
            })

        # --- 3. User List (Table) with Pagination Handling ---
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Safely extract pagination data
            pagination_data = {
                "total_count": self.paginator.page.paginator.count,
                "total_pages": self.paginator.page.paginator.num_pages,
                "current_page": self.paginator.page.number,
                "has_next": self.paginator.page.has_next(),
                "has_previous": self.paginator.page.has_previous(),
            }
            user_results = serializer.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            pagination_data = None
            user_results = serializer.data

        # --- 4. Final Response Combination ---
        response_data = {
            "summary": {
                "total_users": total_user,
                "new_registrations": new_registrations,
                "total_revenue": float(total_revenue),
                "currency": "USD"
            },
            # "earning_chart": full_year_chart,
            "user_table": {
                "pagination": pagination_data,
                "results": user_results
            }
        }

        return api_response(True, "Dashboard data fetched successfully", response_data)


# --- 1. Mobile App API (User Section) ---

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """The user will be able to see and delete their own notifications."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(recipient=self.request.user)

    @swagger_auto_schema(tags=['9. Notifications - App'])
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return api_response(True, "Notifications fetched", self.get_serializer(queryset, many=True).data)

    @swagger_auto_schema(tags=['9. Notifications - App'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_read = True  # Click to mark as read
        instance.save()
        return api_response(True, "Notification details", self.get_serializer(instance).data)

    @swagger_auto_schema(tags=['9. Notifications - App'])
    def destroy(self, request, *args, **kwargs):
        """Figma Trash Icon Works"""
        instance = self.get_object()
        instance.delete()
        return api_response(True, "Notification deleted successfully", None, status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(tags=['9. Notifications - App'])
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """To show the red number on the bell icon"""
        count = Notification.objects.filter(
            recipient=request.user, is_read=False).count()
        return api_response(True, "Unread count fetched", {"unread_count": count})

    @swagger_auto_schema(tags=['9. Notifications - App'])
    @action(detail=True, methods=['patch'], url_path='mark-read')
    def mark_as_read(self, request, pk=None):
        """Mark a specific notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return api_response(True, "Marked as read")


class DeviceTokenViewSet(viewsets.GenericViewSet):
    """After logging into the mobile app, FCM will send the token here."""
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['9. Notifications - App'])
    @action(detail=False, methods=['post'], url_path='register-token')
    def register_token(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            DeviceToken.objects.update_or_create(
                user=request.user,
                token=serializer.validated_data['token'],
                defaults={'platform': serializer.validated_data['platform']}
            )
            return api_response(True, "Device token registered successfully")
        return api_response(False, "Registration failed", serializer.errors, 400)


# --- 2. Admin API (Dashboard Section) ---

class AdminNotificationViewSet(viewsets.GenericViewSet):
    """To control notifications from the admin dashboard"""
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        tags=['Admin - Notification Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'notification_type': openapi.Schema(type=openapi.TYPE_STRING, description="case_update, system_update, etc."),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Optional: specific user ID"),
            },
            required=['notification_type', 'message']
        )
    )
    @action(detail=False, methods=['post'], url_path='send')
    def send_notification(self, request):
        msg_text = request.data.get('message')
        msg_type = request.data.get('notification_type')
        user_id = request.data.get('user_id')

        if user_id:
            # Send to a specific user
            target_user = get_object_or_404(User, id=user_id)
            Notification.objects.create(
                recipient=target_user, sender=request.user, notification_type=msg_type, message=msg_text)
        else:
            # Sending to all users (Broadcast)
            users = User.objects.filter(is_staff=False)
            notifications = [
                Notification(recipient=u, sender=request.user, notification_type=msg_type, message=msg_text) for u in users
            ]
            Notification.objects.bulk_create(notifications)

        return api_response(True, "Notification(s) sent successfully")


# --- Resend OTP API View ---

class ResendOTPApiView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['1. Authentication'])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid email", serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            return api_response(False, "No account found with this email.", None, status.HTTP_404_NOT_FOUND)

        otp_code = generate_otp()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.otp = otp_code
        profile.otp_created_at = timezone.now()
        profile.save()

        # ইমেইল পাঠানো
        try:
            msg = EmailMessage(
                'Resend Verification Code - Pipyrit',
                f'Your new verification code is: {otp_code}. Valid for 5 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            msg.send()
        except Exception:
            return api_response(False, "Failed to send email. Try again later.", None, status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = {
            "email": email,
            "expiresAt": (profile.otp_created_at + timedelta(minutes=5)).isoformat()
        }
        return api_response(True, "A new OTP has been sent to your email.", data)


from rest_framework_simplejwt.views import TokenRefreshView

class CustomTokenRefreshView(TokenRefreshView):

    @swagger_auto_schema(tags=['1. Authentication'])
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            data = {
                "access": response.data.get('access'),
                "refresh": response.data.get('refresh') 
            }
            return api_response(True, "Token refreshed successfully", data)
        
        return api_response(False, "Invalid refresh token", response.data, status.HTTP_401_UNAUTHORIZED)