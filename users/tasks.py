"""
This module contains tasks for the users app.
"""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(
    name="send_verification_email_task",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
)
def send_verification_email_task(user_email, token):
    """
    Task for sending verification emails.
    """
    subject = "Verify Email Address"
    message = f"""
mutation {{
    verifyEmail(token: "{token}") {{
        success
        message
    }}
}}
    """
    result = send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )

    return result
