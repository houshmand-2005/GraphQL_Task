"""
Test GraphQL mutations for the subscriptions app.
"""

from unittest.mock import Mock

from django.test import TestCase
from graphene.test import Client

from core.schema import schema
from subscriptions.models import SubscriptionPlan, UserSubscription
from users.models import CustomUser
from utils.jwt_utils import generate_access_token


class SubscriptionMutationsTest(TestCase):
    """
    Test GraphQL mutations for the subscriptions app.
    """

    def setUp(self):
        self.client = Client(schema)

        self.admin_user = CustomUser.objects.create_user(
            user_name="adminuser",
            email="admin@example.com",
            password="adminpassword123",
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_staff=True,
        )

        self.regular_user = CustomUser.objects.create_user(
            user_name="regularuser",
            email="regular@example.com",
            password="password123",
            first_name="Regular",
            last_name="User",
            is_active=True,
        )

        self.free_plan = SubscriptionPlan.objects.create(
            name="Free",
            description="Basic free plan with limited usage",
            price=0,
            max_characters=5,
            max_conversations=3,
            is_active=True,
            is_default=True,
        )

        self.premium_plan = SubscriptionPlan.objects.create(
            name="Premium",
            description="Premium plan with more features",
            price=9.99,
            max_characters=100,
            max_conversations=10,
            is_active=True,
        )

        self.free_subscription = UserSubscription.objects.create(
            user=self.regular_user,
            plan=self.free_plan,
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

    def test_create_subscription_plan_as_admin(self):
        """Test creating a subscription plan as admin"""
        query = """
        mutation {
        createSubscriptionPlan(
            name: "Pro Plan", 
            description: "Professional plan",
            maxCharacters: 250,
            maxConversations: 25,
            price: 19.99,
            isActive: true
        ) {
            success
            message
        }
        }
        """

        context_value = self._create_mock_context(self.admin_user)
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("data", result)
        self.assertIn("createSubscriptionPlan", result["data"])
        plan_data = result["data"]["createSubscriptionPlan"]
        self.assertTrue(plan_data["success"])

        created_plan = SubscriptionPlan.objects.filter(name="Pro Plan").first()
        self.assertIsNotNone(created_plan)
        self.assertEqual(created_plan.max_characters, 250)
        self.assertEqual(created_plan.max_conversations, 25)

    def test_create_subscription_plan_as_non_admin(self):
        """Test creating a subscription plan as non-admin (should fail)"""
        query = """
        mutation {
          createSubscriptionPlan(
            name: "Another Plan", 
            description: "non-admin",
            maxCharacters: 999,
            maxConversations: 999,
            price: 0
          ) {
            success
            message
          }
        }
        """

        context_value = self._create_mock_context(self.regular_user)
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("errors", result)
        self.assertIn("permission denied", result["errors"][0]["message"].lower())

        self.assertFalse(SubscriptionPlan.objects.filter(name="Another Plan").exists())

    def test_upgrade_subscription(self):
        """Test upgrading a user's subscription plan"""
        query = f"""
        mutation {{
          upgradeSubscription(planId: "{self.premium_plan.id}") {{
            success
            message
            subscription {{
              plan {{
                name
                maxCharacters
                maxConversations
              }}
            }}
          }}
        }}
        """

        context_value = self._create_mock_context(self.regular_user)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL mutation returned errors")
        self.assertIn("data", result)
        self.assertIn("upgradeSubscription", result["data"])

        upgrade_data = result["data"]["upgradeSubscription"]

        self.assertTrue(upgrade_data["success"])
        self.assertIn("Premium", upgrade_data["message"])
        self.assertEqual(upgrade_data["subscription"]["plan"]["name"], "Premium")
        self.assertEqual(upgrade_data["subscription"]["plan"]["maxCharacters"], 100)

        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.subscription.plan, self.premium_plan)

    def test_upgrade_subscription_invalid_plan(self):
        """Test upgrading to an invalid plan ID"""
        query = """
        mutation {
          upgradeSubscription(planId: "999") {
            success
            message
          }
        }
        """

        context_value = self._create_mock_context(self.regular_user)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL mutation returned errors")
        self.assertIn("data", result)
        self.assertIn("upgradeSubscription", result["data"])

        upgrade_data = result["data"]["upgradeSubscription"]

        self.assertFalse(upgrade_data["success"])
        self.assertIn("Invalid plan ID", upgrade_data["message"])

        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.subscription.plan, self.free_plan)

    def test_upgrade_subscription_unauthenticated(self):
        """Test upgrading subscription without authentication"""
        query = f"""
        mutation {{
          upgradeSubscription(planId: "{self.premium_plan.id}") {{
            success
            message
          }}
        }}
        """

        result = self.client.execute(query)

        self.assertIn("errors", result)
        error_msg = result["errors"][0]["message"].lower()
        self.assertTrue("authentication" in error_msg or "meta" in error_msg)
