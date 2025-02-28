"""
This file provide CustomUser model for users app
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.managers import CustomUserManager
from utils.models import BaseModel
from utils.validators import username_validator
from core.configs import EMAIL_VERIFICATION_TOKEN_EXPIRY


class CustomUser(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom user model that supports email as the unique identifier.
    """

    user_name = models.CharField(
        _("user_name"),
        max_length=30,
        unique=True,
        validators=[MinLengthValidator(5), username_validator],
    )
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=30)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without explicitly assigning them."
        ),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts. And also used for email verification."
        ),
    )
    objects = CustomUserManager()

    USERNAME_FIELD = "user_name"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta class for the CustomUser
        """

        verbose_name = _("user")
        verbose_name_plural = _("users")
        constraints = [
            models.UniqueConstraint(
                fields=["user_name", "email"], name="unique_user_email"
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_name} - {self.email}"


class EmailVerificationToken(BaseModel):
    """
    Model to store email verification tokens.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    objects = models.Manager()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                hours=EMAIL_VERIFICATION_TOKEN_EXPIRY
            )
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if the token is still valid (not expired and not used)."""
        return timezone.now() <= self.expires_at and not self.is_used

    def __str__(self):
        return f"{getattr(self.user, 'user_name', 'Unknown')}: {self.token}"
