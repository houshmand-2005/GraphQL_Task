"""
Test cases for the GraphQL queries in the users app.
"""

from unittest.mock import Mock

from django.test import TestCase
from graphene.test import Client

from core.schema import schema
from users.models import CustomUser
from utils.jwt_utils import generate_access_token


class UserQueriesTest(TestCase):
    """
    Test cases for the GraphQL queries in the users app.
    """

    def setUp(self):
        self.client = Client(schema)

        self.user = CustomUser.objects.create_user(
            user_name="testuser",
            email="test@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User",
        )

        self.staff_user = CustomUser.objects.create_user(
            user_name="staffuser",
            email="staff@example.com",
            password="staffpass123",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )

        for i in range(3):
            CustomUser.objects.create_user(
                user_name=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                first_name=f"First{i}",
                last_name=f"Last{i}",
            )

    def _create_mock_context(self, user=None):
        mock_context = Mock()

        if user:
            token = generate_access_token(user)
            mock_context.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        else:
            mock_context.META = {}

        return mock_context

    def test_me_query_authenticated(self):
        """
        Test the me query when the user is authenticated.
        """
        query = """
        query {
          me {
            id
            userName
            email
            firstName
            lastName
          }
        }
        """

        context_value = self._create_mock_context(self.user)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL query returned errors")
        self.assertIn("data", result)
        self.assertIn("me", result["data"])
        self.assertIsNotNone(result["data"]["me"], "The me query returned null")

        user_data = result["data"]["me"]

        self.assertEqual(user_data["userName"], "testuser")
        self.assertEqual(user_data["email"], "test@example.com")
        self.assertEqual(user_data["firstName"], "Test")
        self.assertEqual(user_data["lastName"], "User")

    def test_me_query_unauthenticated(self):
        """
        Test the me query when the user is not authenticated.
        """
        query = """
        query {
          me {
            userName
          }
        }
        """

        context_value = self._create_mock_context()
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("errors", result)
        self.assertIn("Authentication required", result["errors"][0]["message"])

    def test_users_query_as_staff(self):
        """
        Test the users query when the user is a staff user.
        """
        query = """
        query {
          users {
            id
            userName
            email
          }
        }
        """

        context_value = self._create_mock_context(self.staff_user)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL query returned errors")
        self.assertIn("data", result)
        self.assertIn("users", result["data"])
        self.assertIsNotNone(result["data"]["users"], "The users query returned null")

        users_data = result["data"]["users"]
        self.assertEqual(len(users_data), 5)

        usernames = [user["userName"] for user in users_data]
        self.assertIn("testuser", usernames)
        self.assertIn("staffuser", usernames)

    def test_users_query_as_regular_user(self):
        """
        Test the users query when the user is a regular user.
        """
        query = """
        query {
          users {
            userName
          }
        }
        """

        context_value = self._create_mock_context(self.user)
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("errors", result)
        self.assertIn("Permission denied", result["errors"][0]["message"])

    def test_users_query_unauthenticated(self):
        """
        Test the users query when the user is not authenticated
        """
        query = """
        query {
          users {
            userName
          }
        }
        """

        context_value = self._create_mock_context()
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("errors", result)
        self.assertIn("Authentication required", result["errors"][0]["message"])
