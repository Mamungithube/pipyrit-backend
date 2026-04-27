from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
from .utils import create_notification
from user.utils import create_notification
from .models import User, Profile ,Notification



from django.utils import timezone
from datetime import timedelta
from payment.models import UserSubscription
from django.db.models.signals import post_save
from django.dispatch import receiver
from cases.models import ImmigrationCase
from quizzes.models import UserQuizResult, InterviewResult
from user.models import User

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def start_free_trial(sender, instance, created, **kwargs):
    if created:
        # Set a 7-day trial during registration
        expiry = timezone.now() + timedelta(days=7)
        UserSubscription.objects.create(
            user=instance, 
            expiry_date=expiry, 
            is_active=True, # Will remain active during the trial period.
            is_trial_used=True
        )



@receiver(post_save, sender=ImmigrationCase)
def notify_case_added(sender, instance, created, **kwargs):
    if created:
        # ইউজারকে জানানো
        Notification.objects.create(
            recipient=instance.user,
            notification_type='case_update',
            message=f"Success! Your case '{instance.title}' has been added.",
            is_read=False
        )
        
        # অ্যাডমিনকে জানানো
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notification_type='case_update',
                message=f"New case added by {instance.user.full_name}: {instance.title}",
                is_read=False
            )

@receiver(post_save, sender=UserQuizResult)
def notify_quiz_completed(sender, instance, created, **kwargs):
    if created:
        # ১. ইউজারকে তার স্কোর জানানো
        msg = f"You scored {instance.correct_answers} out of {instance.total_questions} in the Quick Quiz!"
        create_notification(instance.user, 'quiz_reminder', msg)
        
        # ২. অ্যাডমিনকে জানানো
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            create_notification(admin, 'quiz_reminder', f"{instance.user.full_name} completed a quiz with {instance.total_points_earned} points.")

@receiver(post_save, sender=InterviewResult)
def notify_interview_completed(sender, instance, created, **kwargs):
    if created:
        # ইউজার এবং অ্যাডমিনকে ইন্টারভিউ এবং কনফিডেন্স লেভেল জানানো
        create_notification(instance.user, 'system_update', f"Interview finished! Confidence level: {instance.confidence_level}%")

@receiver(post_save, sender=ImmigrationCase)
def auto_notify_case(sender, instance, created, **kwargs):
    if created:
        # ১. ইউজারকে নোটিফিকেশন পাঠানো
        Notification.objects.create(
            recipient=instance.user,
            notification_type='case_update',
            message=f"Success! Your case '{instance.title}' has been added.",
            is_read=False
        )
        # ২. অ্যাডমিনকে জানানো (যাতে ড্যাশবোর্ডে অ্যাডমিন দেখতে পায়)
        from .models import User
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notification_type='case_update',
                message=f"Alert: {instance.user.full_name} added a new case.",
                is_read=False
            )

# ইউজার কুইজ শেষ করলে নোটিফিকেশন
@receiver(post_save, sender=UserQuizResult)
def auto_notify_quiz(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.user,
            notification_type='quiz_reminder',
            message=f"Well done! You earned {instance.total_points_earned} points in the quiz.",
            is_read=False
        )