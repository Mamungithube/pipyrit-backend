from rest_framework import serializers
from .models import DeviceToken, User, Profile, Notification


class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    
    def get_profile_picture(self, obj):
        request = self.context.get('request')
        print("request:", request)
        print("profile_picture:", obj.profile_picture)
        if obj.profile_picture and request:
            return request.build_absolute_uri(obj.profile_picture.url)
        return None
    
    class Meta:
        model = Profile
        fields = ['profile_picture', 'language',
                  'total_points', 'confidence_level', 'is_verified']
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'full_name' in user_data:
            instance.user.full_name = user_data['full_name']
            instance.user.save()
        return super().update(instance, validated_data)

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        return ProfileSerializer(obj.profile, context=self.context).data

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'is_staff', 'profile']


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'

    def get_time_ago(self, obj):
        # ফিগমা অনুযায়ী "5 min ago" বা "1 hour ago" দেখানোর জন্য
        from django.utils.timesince import timesince
        if not obj.created_at:
            return "Just now"
        return timesince(obj.created_at).split(',')[0] + " ago"

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token', 'platform']

class AdminUserManagementSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(source='profile.profile_picture', read_only=True)
    registration_date = serializers.DateTimeField(source='date_joined', format="%B %d, %Y", read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'registration_date', 'is_active', 'profile_picture']