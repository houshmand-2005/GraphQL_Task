"""
This file provides admin classes for chat app
"""

from django.contrib import admin

from .models import Conversation, Message


class ConversationAdmin(admin.ModelAdmin):
    """Conversation admin class for conversation model in admin panel"""

    list_display = (
        "id",
        "title",
        "owner",
        "created_at",
        "update_at",
        "get_member_count",
    )
    search_fields = (
        "title",
        "owner__user_name",
        "owner__email",
    )
    list_filter = (
        "created_at",
        "owner",
    )
    readonly_fields = (
        "created_at",
        "update_at",
    )
    filter_horizontal = ("members",)
    date_hierarchy = "created_at"

    def get_member_count(self, obj):
        """Return the number of members in the conversation."""
        return obj.members.count()

    get_member_count.short_description = "Member Count"


class MessageAdmin(admin.ModelAdmin):
    """Message admin class for message model in admin panel"""

    list_display = (
        "id",
        "get_short_text",
        "sender",
        "conversation",
        "created_at",
    )
    search_fields = (
        "text",
        "sender__user_name",
        "conversation__title",
    )
    list_filter = (
        "created_at",
        "sender",
        "conversation",
    )
    readonly_fields = (
        "created_at",
        "update_at",
    )
    date_hierarchy = "created_at"

    def get_short_text(self, obj):
        """Return a shortened version of the message text."""
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    get_short_text.short_description = "Message"


admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
