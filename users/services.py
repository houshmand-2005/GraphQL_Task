"""
This module contains services for the users app.
"""

from django.contrib.auth import get_user_model

from subscriptions.services import get_or_create_user_subscription

from users.models import EmailVerificationToken
from users.tasks import send_verification_email_task

User = get_user_model()


def create_user(
    user_name: str, email: str, password: str, first_name: str, last_name: str
):
    """
    Create a new user with the given details.
    """
    user = User.objects.create_user(
        user_name=user_name,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )
    get_or_create_user_subscription(user=user)
    verification_token = EmailVerificationToken.objects.create(user=user)
    send_verification_email_task.delay(email, str(verification_token.token))
    return user
