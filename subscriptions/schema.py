"""
GraphQL schema for the subscriptions app.
"""

import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError

from subscriptions.models import SubscriptionPlan, UserSubscription
from subscriptions.services import (
    change_user_plan,
    check_conversation_limits,
    get_or_create_user_subscription,
)
from utils.jwt_utils import get_authenticated_user


class SubscriptionPlanType(DjangoObjectType):
    """GraphQL type for SubscriptionPlan model"""

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta class for SubscriptionPlanType
        """

        model = SubscriptionPlan


class UserSubscriptionType(DjangoObjectType):
    """GraphQL type for UserSubscription model with computed fields"""

    conversations_remaining = graphene.Int()

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta class for UserSubscriptionType
        """

        model = UserSubscription

    def resolve_conversations_remaining(self, info):
        """Calculate and return remaining conversation limit"""
        user = get_authenticated_user(info)
        _, remaining = check_conversation_limits(user)
        return remaining


class Query(graphene.ObjectType):
    """Queries for the subscriptions app"""

    subscription_plans = graphene.List(
        SubscriptionPlanType, description="List all active subscription plans"
    )

    my_subscription = graphene.Field(
        UserSubscriptionType, description="Get current user's subscription details"
    )

    def resolve_subscription_plans(self, info):  # pylint: disable=unused-argument
        """Return all active subscription plans"""
        return SubscriptionPlan.objects.filter(is_active=True)

    def resolve_my_subscription(self, info):
        """Return the current user's subscription"""
        user = get_authenticated_user(info)
        return get_or_create_user_subscription(user)


class CreateSubscriptionPlan(graphene.Mutation):
    """Mutation to create a new subscription plan (admin only)"""

    success = graphene.Boolean()
    plan = graphene.Field(SubscriptionPlanType)
    message = graphene.String()

    class Arguments:  # pylint: disable=too-few-public-methods
        """
        Arguments for creating a subscription plan
        """

        name = graphene.String(
            required=True, description="Name of the subscription plan"
        )
        description = graphene.String(
            required=True, description="Description of the plan"
        )
        max_characters = graphene.Int(
            required=True, description="Maximum characters allowed"
        )
        max_conversations = graphene.Int(
            required=True, description="Maximum conversations allowed"
        )
        price = graphene.Float(description="Price of the subscription plan")
        is_active = graphene.Boolean(description="Whether the plan is active")

    def mutate(
        self,
        info,
        name,
        description,
        max_characters,
        max_conversations,
        price=0,
        is_active=True,
        is_default=False,
    ):  # pylint: disable=too-many-arguments
        """Create a new subscription plan (admin only)"""
        user = get_authenticated_user(info)

        if not user.is_staff:
            raise GraphQLError(
                "Permission denied. Only administrators can create subscription plans."
            )

        try:
            if SubscriptionPlan.objects.filter(name=name).exists():
                return CreateSubscriptionPlan(
                    success=False,
                    message=f"A subscription plan with the name '{name}' already exists",
                )
            plan = SubscriptionPlan.objects.create(
                name=name,
                description=description,
                max_characters=max_characters,
                max_conversations=max_conversations,
                price=price,
                is_active=is_active,
                is_default=is_default,
            )

            return CreateSubscriptionPlan(
                success=True,
                plan=plan,
                message=f"Subscription plan '{name}' created successfully",
            )

        except Exception as exc:  # pylint: disable=broad-except
            return CreateSubscriptionPlan(
                success=False, message=f"Error creating subscription plan: {str(exc)}"
            )


class UpgradeSubscription(graphene.Mutation):
    """Mutation to upgrade/change user's subscription plan"""

    success = graphene.Boolean()
    subscription = graphene.Field(UserSubscriptionType)
    message = graphene.String()

    class Arguments:  # pylint: disable=too-few-public-methods
        """
        Arguments for the mutation
        """

        plan_id = graphene.ID(
            required=True, description="ID of the subscription plan to upgrade to"
        )

    def mutate(self, info, plan_id):
        """Change user's subscription plan"""
        user = get_authenticated_user(info)

        try:
            success = change_user_plan(user, plan_id)
            if not success:
                return UpgradeSubscription(
                    success=False, message="Invalid plan ID or plan is not active"
                )

            subscription = get_or_create_user_subscription(user)
            return UpgradeSubscription(
                success=True,
                subscription=subscription,
                message=f"Successfully upgraded to {subscription.plan.name} plan",
            )
        except Exception as exc:  # pylint: disable=broad-except
            return UpgradeSubscription(
                success=False, message=f"Error upgrading subscription: {str(exc)}"
            )


class Mutation(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Mutations for the subscriptions app"""

    upgrade_subscription = UpgradeSubscription.Field(
        description="Upgrade or change the current user's subscription plan"
    )
    create_subscription_plan = CreateSubscriptionPlan.Field(
        description="Create a new subscription plan (admin only)"
    )
