"""
This file provide 'BaseModel' for all models
"""

from django.db import models


class BaseModel(models.Model):
    """Base model for all models"""

    created_at = models.DateTimeField(("created_date"), auto_now_add=True)
    update_at = models.DateTimeField(("update_date"), auto_now=True)

    class Meta:  # pylint: disable=missing-class-docstring,too-few-public-methods
        abstract = True
