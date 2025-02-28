"""
This file is used to configure the app name for the users app.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuration class for the users
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
