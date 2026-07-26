"""
user/services.py
~~~~~~~~~~~~~~~~
Business logic for user authentication flows (OTP, email dispatch).
Views remain thin — they only handle HTTP; all operations live here.
"""

import threading

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from .models import Profile
from .utils import generate_otp


# ── Internal Helper ───────────────────────────────────────────────────────────

def _send_async_email(email_message: EmailMessage) -> None:
    """Dispatch a pre-built EmailMessage in a background thread (fire-and-forget)."""
    try:
        email_message.send()
    except Exception:
        pass


# ── OTP Services ──────────────────────────────────────────────────────────────

def create_and_save_otp(user) -> str:
    """
    Generates a new OTP, saves it to the user's profile with the current
    timestamp, and returns the raw OTP string.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    otp_code = generate_otp()
    profile.otp = otp_code
    profile.otp_created_at = timezone.now()
    profile.save()
    return otp_code


def send_verification_email(to_email: str, otp_code: str) -> None:
    """
    Sends an account-verification OTP email asynchronously.
    Raises no exception on failure — caller decides how to handle.
    """
    msg = EmailMessage(
        subject='Verify your email - Pipyrit',
        body=f'Your verification code is: {otp_code}. It will expire in 5 minutes.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    threading.Thread(target=_send_async_email, args=(msg,), daemon=True).start()


def send_password_reset_email(to_email: str, otp_code: str) -> None:
    """
    Sends a password-reset OTP email asynchronously.
    Raises no exception on failure — caller decides how to handle.
    """
    msg = EmailMessage(
        subject='Reset your password - Pipyrit',
        body=f'Your password reset code is: {otp_code}. Valid for 5 minutes.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    threading.Thread(target=_send_async_email, args=(msg,), daemon=True).start()
