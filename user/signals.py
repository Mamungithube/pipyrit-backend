from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import User, Profile, Notification
from .utils import create_notification
from payment.models import UserSubscription
from cases.models import ImmigrationCase
from quizzes.models import UserQuizResult, InterviewResult


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
            is_active=True,  # Will remain active during the trial period.
            is_trial_used=True
        )


@receiver(post_save, sender=ImmigrationCase)
def notify_case_added(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.user,
            notification_type='case_update',
            message=f"Success! Your case '{instance.title}' has been added.",
            is_read=False
        )

        admins = User.objects.filter(is_staff=True)
        Notification.objects.bulk_create([
            Notification(
                recipient=admin,
                notification_type='case_update',
                message=f"New case added by {instance.user.full_name}: {instance.title}",
                is_read=False
            )
            for admin in admins
        ])


@receiver(post_save, sender=UserQuizResult)
def notify_quiz_completed(sender, instance, created, **kwargs):
    if created:
        msg = f"Well done! You earned {instance.total_points_earned} points in the quiz."
        create_notification(instance.user, 'quiz_reminder', msg)

        admin_users = User.objects.filter(is_staff=True)
        Notification.objects.bulk_create([
            Notification(
                recipient=admin,
                notification_type='quiz_reminder',
                message=f"{instance.user.full_name} completed a quiz with {instance.total_points_earned} points.",
                is_read=False
            )
            for admin in admin_users
        ])


@receiver(post_save, sender=InterviewResult)
def notify_interview_completed(sender, instance, created, **kwargs):
    if created:
        create_notification(
            instance.user,
            'system_update',
            f"Interview finished! Confidence level: {instance.confidence_level}%"
        )