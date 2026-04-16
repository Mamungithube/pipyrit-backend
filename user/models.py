from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

"""=========================Custom User Manager========================="""


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


"""=========================Custom User Model========================="""


class User(AbstractUser):
    username = None  # ইমেইল দিয়ে লগইন হবে তাই ইউজারনেম বাদ
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    def __str__(self):
        return self.full_name or self.email


"""=========================Profile Model========================="""


class Profile(models.Model):
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('hc', 'Haitian Creole'),
        ('es', 'Spanish'),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    otp = models.CharField(max_length=4, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profiles/', blank=True, null=True)

    # অ্যাপের ফিচারের জন্য লজিক্যাল ফিল্ডস
    language = models.CharField(
        max_length=10, choices=LANGUAGE_CHOICES, default='en')
    total_points = models.IntegerField(default=0)
    confidence_level = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.full_name or self.user.email


"""=========================Notification Model========================="""


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('case_update', 'Case Update'),
        ('quiz_reminder', 'Quiz Reminder'),
        ('subscription_alert', 'Subscription Alert'),
        ('system_update', 'System Update'),
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    # যে ইউজার বা সিস্টেম নোটিফিকেশন পাঠালো
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='sent_notifications',
        null=True, blank=True
    )
    notification_type = models.CharField(
        max_length=30, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.email}"


class DeviceToken(models.Model):
    PLATFORM_CHOICES = (
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='device_tokens'
    )
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(
        max_length=20, choices=PLATFORM_CHOICES, default='web')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.platform}"
