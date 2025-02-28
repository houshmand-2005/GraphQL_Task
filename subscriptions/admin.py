"""
This file provide SubscriptionAdmin class for subscriptions app
"""

from django.contrib import admin

from subscriptions.models import SubscriptionPlan, UserSubscription


class SubscriptionAdmin(admin.ModelAdmin):
    """SubscriptionPlan admin class for subscription model in admin panel"""

    list_display = (
        "id",
        "name",
        "price",
        "description",
        "max_characters",
        "max_conversations",
        "is_active",
        "created_at",
        "update_at",
    )
    search_fields = (
        "name",
        "price",
        "description",
    )

    date_hierarchy = "created_at"


class UserSubscriptionAdmin(admin.ModelAdmin):
    """UserSubscription admin class for user subscriptions in admin panel"""

    list_display = (
        "id",
        "user",
        "plan",
        "created_at",
        "update_at",
    )
    list_filter = (
        "plan",
        "created_at",
    )
    date_hierarchy = "created_at"


admin.site.register(SubscriptionPlan, SubscriptionAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
