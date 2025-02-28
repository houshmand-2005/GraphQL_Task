"""
Test GraphQL queries for the subscriptions app.
"""

from unittest.mock import Mock, patch

from django.test import TestCase
from graphene.test import Client

from core.schema import schema
from subscriptions.models import SubscriptionPlan, UserSubscription
from users.models import CustomUser
from utils.jwt_utils import generate_access_token


class SubscriptionQueriesTest(TestCase):  # pylint: disable=too-many-instance-attributes
    """
    Test GraphQL queries for the subscriptions app.
    """

    def setUp(self):
        self.client = Client(schema)

        self.user = CustomUser.objects.create_user(
            user_name="testuser",
            email="test@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )

        self.admin_user = CustomUser.objects.create_user(
            user_name="adminuser",
            email="admin@example.com",
            password="adminpassword123",
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_staff=True,
        )

        self.free_plan = SubscriptionPlan.objects.create(
            name="Free",
            description="Basic free plan",
            price=0,
            max_characters=100,
            max_conversations=3,
            is_active=True,
            is_default=True,
        )

        self.inactive_plan = SubscriptionPlan.objects.create(
            name="Inactive Plan",
            description="This plan should not show up in queries",
            price=5.99,
            max_characters=500,
            max_conversations=10,
            is_active=False,
        )

        self.premium_plan = SubscriptionPlan.objects.create(
            name="Premium",
            description="Premium plan with more features",
            price=9.99,
            max_characters=1000,
            max_conversations=10,
            is_active=True,
        )

        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.free_plan,
        )

        self.admin_subscription = UserSubscription.objects.create(
            user=self.admin_user,
            plan=self.premium_plan,
        )

    def _create_mock_context(self, user=None):
        """Helper to create context with authentication"""
        mock_context = Mock()

        if user:
            token = generate_access_token(user)
            mock_context.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
            mock_context.user = user
        else:
            mock_context.META = {}

        return mock_context

    def test_subscription_plans_authenticated(self):
        """Test retrieving subscription plans as authenticated user"""
        query = """
        query {
          subscriptionPlans {
            id
            name
            description
            price
            maxCharacters
            maxConversations
            isActive
          }
        }
        """

        context_value = self._create_mock_context(self.user)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL query returned errors")
        self.assertIn("data", result)
        self.assertIn("subscriptionPlans", result["data"])

        plans_data = result["data"]["subscriptionPlans"]
        plan_names = [plan["name"] for plan in plans_data]

        self.assertIn("Free", plan_names)
        self.assertIn("Premium", plan_names)

        self.assertNotIn("Inactive Plan", plan_names)

        self.assertEqual(len(plans_data), 2)

    def test_my_subscription_authenticated(self):
        """Test retrieving user's subscription details"""
        query = """
        query {
          mySubscription {
            plan {
              name
              maxCharacters
              maxConversations
            }
            conversationsRemaining
          }
        }
        """

        context_value = self._create_mock_context(self.user)

        with patch(
            "subscriptions.services.check_conversation_limits", return_value=(True, 2)
        ):
            result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL query returned errors")
        self.assertIn("data", result)
        self.assertIn("mySubscription", result["data"])

        subscription_data = result["data"]["mySubscription"]
        self.assertEqual(subscription_data["plan"]["name"], "Free")
        self.assertEqual(subscription_data["plan"]["maxConversations"], 3)
        self.assertEqual(subscription_data["conversationsRemaining"], 2)

    def test_my_subscription_unauthenticated(self):
        """Test retrieving subscription details without authentication"""
        query = """
        query {
          mySubscription {
            plan {
              name
            }
          }
        }
        """

        result = self.client.execute(query)

        self.assertIn("errors", result)
        error_msg = result["errors"][0]["message"].lower()
        self.assertTrue("authentication" in error_msg or "meta" in error_msg)
