"""
Validators for the application
"""

from django.core.validators import RegexValidator


def username_validator(username: str) -> str:
    """
    Validate username to consist of only English letters And without any spaces
    """
    return RegexValidator(
        regex=r"^[a-zA-Z0-9]+$",
        message="Username must consist of only English letters And without any spaces",
    )(username)
