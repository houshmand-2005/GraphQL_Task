"""
This module contains models related to subscription plans.
"""

from django.conf import settings
from django.db import models

from utils.models import BaseModel


class SubscriptionPlan(BaseModel):
    """
    Model for different subscription plan tiers.
    Each plan has specific limits for characters and conversations.
    """

    name = models.CharField(max_length=50)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_characters = models.PositiveIntegerField(help_text="Maximum characters allowed")
    max_conversations = models.PositiveIntegerField(
        help_text="Maximum conversations allowed"
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False, help_text="Set as default plan for new users"
    )

    objects = models.Manager()

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta class for SubscriptionPlan model.
        """

        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} - {self.is_active}"


class UserSubscription(BaseModel):
    """
    Links a user to their subscription plan and tracks usage.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscribers",
    )

    objects = models.Manager()

    def __str__(self):
        return f"{getattr(self.user, 'user_name', 'Unknown')} - {self.plan.name}"
