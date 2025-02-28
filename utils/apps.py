"""
This file is used to configure the app name for the utils app.
"""

from django.apps import AppConfig


class UtilsConfig(AppConfig):
    """
    Configuration class for the utils
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "utils"
