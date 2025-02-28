"""
This module contains the models for the chat application.
"""

from django.conf import settings
from django.db import models

from utils.models import BaseModel


class Conversation(BaseModel):
    """
    This model is used to store the conversations between the users.
    """

    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_conversations",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="joined_conversations", blank=True
    )

    objects = models.Manager()

    def __str__(self):
        return f"{self.title}"


class Message(BaseModel):
    """
    The message model is used to store the messages sent by the users.
    """

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages"
    )
    text = models.TextField()

    objects = models.Manager()

    def __str__(self):
        return f"{getattr(self.sender, 'user_name', 'Unknown')}: {str(self.text)[:20]}"
