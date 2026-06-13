import random

def generate_otp():
    return str(random.randint(1000, 9999))

from .models import Notification, User

def create_notification(recipient, msg_type, message, sender=None):
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=msg_type,
        message=message,
        is_read=False
    )


