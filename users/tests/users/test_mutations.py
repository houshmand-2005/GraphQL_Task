"""
Test user mutations.
"""

from unittest.mock import patch

from django.test import TestCase
from graphene.test import Client

from core.schema import schema
from users.models import CustomUser, EmailVerificationToken


class BasicUserMutationsTest(TestCase):
    """
    Test basic user mutations.
    """

    def setUp(self):
        self.client = Client(schema)

        self.test_user = CustomUser.objects.create_user(
            user_name="testuser",
            email="test@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )

    @patch("users.tasks.send_verification_email_task.delay")
    def test_register_user(self, mock_task):
        """Test basic user registration"""
        query = """
        mutation {
          register(
            userName: "newuser", 
            email: "new@example.com",
            password: "password123",
            firstName: "New",
            lastName: "User"
          ) {
            user {
              userName
              email
              isActive
            }
          }
        }
        """

        result = self.client.execute(query)

        self.assertIn("data", result)
        self.assertIn("register", result["data"])
        self.assertIn("user", result["data"]["register"])

        user_data = result["data"]["register"]["user"]

        self.assertEqual(user_data["userName"], "newuser")
        self.assertEqual(user_data["email"], "new@example.com")
        self.assertFalse(user_data["isActive"])

        self.assertTrue(CustomUser.objects.filter(user_name="newuser").exists())

        mock_task.assert_called_once()

    def test_login_user(self):
        """Test user login with correct credentials"""
        query = """
        mutation {
          login(username: "testuser", password: "testpassword123") {
            user {
              userName
              email
            }
            token {
              access
              refresh
            }
          }
        }
        """

        result = self.client.execute(query)

        self.assertIn("data", result)
        self.assertIn("login", result["data"])
        self.assertIn("user", result["data"]["login"])
        self.assertIn("token", result["data"]["login"])

        user_data = result["data"]["login"]["user"]

        self.assertEqual(user_data["userName"], "testuser")
        self.assertEqual(user_data["email"], "test@example.com")

        token_data = result["data"]["login"]["token"]

        self.assertIsNotNone(token_data["access"])
        self.assertIsNotNone(token_data["refresh"])

    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        query = """
        mutation {
          login(username: "testuser", password: "wrongpassword") {
            user {
              userName
            }
            token {
              access
            }
          }
        }
        """

        result = self.client.execute(query)

        self.assertIn("errors", result)
        self.assertIn("Invalid credentials", result["errors"][0]["message"])

    def test_email_verification(self):
        """Test email verification with valid token"""
        inactive_user = CustomUser.objects.create_user(
            user_name="inactive",
            email="inactive@example.com",
            password="password123",
            first_name="Inactive",
            last_name="User",
            is_active=False,
        )

        token = EmailVerificationToken.objects.create(user=inactive_user)

        query = f'''
        mutation {{
          verifyEmail(token: "{token.token}") {{
            success
            message
            token {{
              access
              refresh
            }}
          }}
        }}
        '''

        result = self.client.execute(query)

        self.assertIn("data", result)
        self.assertIn("verifyEmail", result["data"])

        verification_result = result["data"]["verifyEmail"]

        self.assertTrue(verification_result["success"])
        self.assertIn("verified successfully", verification_result["message"])
        self.assertIsNotNone(verification_result["token"]["access"])

        inactive_user.refresh_from_db()
        self.assertTrue(inactive_user.is_active)
