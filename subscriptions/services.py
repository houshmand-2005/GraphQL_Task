"""
Services for subscription management
"""

from django.core.exceptions import ObjectDoesNotExist

from subscriptions.models import SubscriptionPlan, UserSubscription


def get_default_plan():
    """Get the default subscription plan or create one if none exists."""
    default_plan = SubscriptionPlan.objects.filter(is_default=True).first()

    if not default_plan:
        default_plan = SubscriptionPlan.objects.create(
            name="Free",
            description="Basic free plan with limited usage",
            price=0,
            max_characters=5,
            max_conversations=3,
            is_active=True,
            is_default=True,
        )

    return default_plan


def get_or_create_user_subscription(user):
    """
    Get existing subscription for user or create a new one with default plan.
    """
    try:
        return user.subscription
    except ObjectDoesNotExist:
        default_plan = get_default_plan()
        return UserSubscription.objects.create(user=user, plan=default_plan)


def check_message_limits(user, message_length):
    """
    Check if user can send a message with the given length.

    Returns:
        tuple: (allowed (bool), remaining (int))
    """
    subscription = get_or_create_user_subscription(user)
    remaining = subscription.plan.max_characters - message_length
    if remaining >= 0:
        return True, remaining
    return False, remaining


def check_conversation_limits(user):
    """
    Check if user can create a new conversation.

    Returns:
        tuple: (allowed (bool), remaining (int))
    """
    subscription = get_or_create_user_subscription(user)
    conversation_count = user.owned_conversations.count()

    # we add 1 to the conversation count for the new conversation as well
    remaining = subscription.plan.max_conversations - (conversation_count + 1)
    if remaining >= 0:
        return True, remaining
    return False, remaining


def change_user_plan(user, plan_id):
    """
    Change user's subscription plan.

    Returns:
        bool: True if successful
    """
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        subscription = get_or_create_user_subscription(user)
        subscription.plan = plan
        subscription.save()
        return True
    except ObjectDoesNotExist:
        return False
