"""
This file provide UserAdmin class for users app
"""

from django.contrib import admin

from users.models import CustomUser, EmailVerificationToken


class UserAdmin(admin.ModelAdmin):
    """User admin class for user model in admin panel"""

    list_display = (
        "id",
        "user_name",
        "first_name",
        "last_name",
        "is_active",
        "is_superuser",
        "is_staff",
        "created_at",
        "update_at",
    )
    search_fields = (
        "user_name",
        "email",
        "first_name",
        "last_name",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )


class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin class for email verification token model"""

    list_display = (
        "id",
        "token",
        "user",
        "expires_at",
        "is_used",
        "created_at",
        "update_at",
    )
    list_filter = (
        "is_used",
        "created_at",
    )
    date_hierarchy = "created_at"


admin.site.register(CustomUser, UserAdmin)
admin.site.register(EmailVerificationToken, EmailVerificationTokenAdmin)
