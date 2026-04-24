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
                "user": UserSerializer(user, context={'request': request}).data  # ✅
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

        if not user:
            return api_response(False, "Invalid or expired OTP.", None, status.HTTP_400_BAD_REQUEST)

        profile, _ = Profile.objects.get_or_create(user=user)

        if profile.otp != otp:
            return api_response(False, "Invalid or expired OTP.", None, status.HTTP_400_BAD_REQUEST)

        if not profile.otp_created_at:
            return api_response(False, "OTP has expired.", None, status.HTTP_400_BAD_REQUEST)

        expiry_time = profile.otp_created_at + timedelta(minutes=5)
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

        if not user:
            return api_response(False, "Request unauthorized or OTP invalid.", None, status.HTTP_401_UNAUTHORIZED)

        profile, _ = Profile.objects.get_or_create(user=user)

        if profile.otp != otp:                     # ← profile ব্যবহার করো
            return api_response(False, "Request unauthorized or OTP invalid.", None, status.HTTP_401_UNAUTHORIZED)

        user.set_password(new_password)
        user.save()

        profile.otp = None                         # ← profile ব্যবহার করো
        profile.save()

        return api_response(True, "Password has been reset successfully. You can now login.")


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

    # এটিই আপনার স্ক্রিনশটে Raw ডাটা দিচ্ছিল, এখন ঠিক করা হলো:
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

    # ডিলিট রেসপন্স ঠিক করা হলো:
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

        # ✅ full_name আলাদাভাবে User model-এ save করো
        full_name = request.data.get('full_name')
        if full_name:
            instance.user.full_name = full_name
            instance.user.save()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
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
    ফিগমা স্ক্রিন ১০: ড্যাশবোর্ড হোম।
    একটি মাত্র এপিআই এন্ডপয়েন্ট যা স্ট্যাটাস কার্ড, ১২ মাসের চার্ট এবং পেজিনেটেড ইউজার লিস্ট দিবে।
    """
    permission_classes = [IsAdminUser]
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = AdminUserManagementSerializer
    pagination_class = CustomPagination

    @swagger_auto_schema(tags=['Admin - Dashboard'])
    def list(self, request, *args, **kwargs):
        # --- ১. টপ কার্ডস ও স্ট্যাটস ক্যালকুলেশন ---
        total_user = User.objects.filter(is_staff=False).count()
        
        # এই মাসের রেজিস্ট্রেশন কাউন্ট
        current_month = timezone.now().month
        new_registrations = User.objects.filter(
            is_staff=False, 
            date_joined__month=current_month
        ).count()
        
        # টোটাল রেভিনিউ
        total_revenue = Transaction.objects.filter(
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # --- ২. আর্নিং সামারি চার্ট ডাটা (১২ মাসের ডাটা ফিক্স) ---
        # ডাটাবেস থেকে শুধু ওই মাসগুলো আনা যেগুলোতে আয় হয়েছে
        chart_stats = Transaction.objects.filter(
            status='completed'
        ).annotate(
            month=ExtractMonth('created_at')
        ).values('month').annotate(total=Sum('amount')).order_by('month')

        # কুয়েরিসেটকে ডিকশনারিতে রূপান্তর (সহজে মেলাবার জন্য)
        stats_dict = {item['month']: item['total'] for item in chart_stats}

        # ১২ মাসের পূর্ণাঙ্গ লিস্ট তৈরি (ফিগমা অনুযায়ী Jan-Dec)
        full_year_chart = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i in range(1, 13):
            full_year_chart.append({
                "month_index": i,
                "month_name": month_names[i-1],
                "total": float(stats_dict.get(i, 0)) # আয় না থাকলে ০.০
            })

        # --- ৩. ইউজার লিস্ট (টেবিল) উইথ পেজিনেশন হ্যান্ডলিং ---
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # পেজিনেশন ডাটা নিরাপদভাবে বের করা
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

        # --- ৪. ফাইনাল রেসপন্স কম্বাইন করা ---
        response_data = {
            "summary": {
                "total_users": total_user,
                "new_registrations": new_registrations,
                "total_revenue": float(total_revenue),
                "currency": "USD"
            },
            "earning_chart": full_year_chart,
            "user_table": {
                "pagination": pagination_data,
                "results": user_results
            }
        }

        return api_response(True, "Dashboard data fetched successfully", response_data)
    

from .models import Notification, DeviceToken
from .serializers import NotificationSerializer, DeviceTokenSerializer


# --- ১. মোবাইল অ্যাপ এপিআই (ইউজার সেকশন) ---

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ইউজার তার নিজের নোটিফিকেশন দেখবে এবং ডিলিট করতে পারবে"""
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
        instance.is_read = True # ক্লিক করলে পড়া হয়েছে হিসেবে মার্ক হবে
        instance.save()
        return api_response(True, "Notification details", self.get_serializer(instance).data)

    @swagger_auto_schema(tags=['9. Notifications - App'])
    def destroy(self, request, *args, **kwargs):
        """ফিগমার ট্র্যাশ আইকন এর কাজ"""
        instance = self.get_object()
        instance.delete()
        return api_response(True, "Notification deleted successfully", None, status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(tags=['9. Notifications - App'])
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """বেল আইকনে লাল সংখ্যাটি দেখানোর জন্য"""
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return api_response(True, "Unread count fetched", {"unread_count": count})
    
    @swagger_auto_schema(tags=['9. Notifications - App'])
    @action(detail=True, methods=['patch'], url_path='mark-read')
    def mark_as_read(self, request, pk=None):
        """একটি নির্দিষ্ট নোটিফিকেশন পড়া হয়েছে হিসেবে মার্ক করা"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return api_response(True, "Marked as read")


class DeviceTokenViewSet(viewsets.GenericViewSet):
    """মোবাইল অ্যাপ লগইন করার পর FCM টোকেন এখানে পাঠাবে"""
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


# --- ২. অ্যাডমিন এপিআই (ড্যাশবোর্ড সেকশন) ---

class AdminNotificationViewSet(viewsets.GenericViewSet):
    """অ্যাডমিন ড্যাশবোর্ড থেকে নোটিফিকেশন কন্ট্রোল করার জন্য"""
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
            # নির্দিষ্ট একজন ইউজারকে পাঠানো
            target_user = get_object_or_404(User, id=user_id)
            Notification.objects.create(recipient=target_user, sender=request.user, notification_type=msg_type, message=msg_text)
        else:
            # সব ইউজারকে পাঠানো (Broadcast)
            users = User.objects.filter(is_staff=False)
            notifications = [
                Notification(recipient=u, sender=request.user, notification_type=msg_type, message=msg_text) for u in users
            ]
            Notification.objects.bulk_create(notifications)

        return api_response(True, "Notification(s) sent successfully")