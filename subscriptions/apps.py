"""
This file is used to configure the subscriptions app.
"""

from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    """
    Configuration class for the subscriptions
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "subscriptions"
