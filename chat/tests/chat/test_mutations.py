"""
Test GraphQL mutations for the chat app.
"""

from unittest.mock import Mock, patch

from django.test import TestCase
from graphene.test import Client

from chat.models import Conversation, Message
from core.schema import schema
from subscriptions.models import SubscriptionPlan, UserSubscription
from users.models import CustomUser
from utils.jwt_utils import generate_access_token


class ChatMutationsTest(TestCase):  # pylint: disable=too-many-instance-attributes
    """
    Test GraphQL mutations for the chat app.
    """

    def setUp(self):
        self.client = Client(schema)

        self.user1 = CustomUser.objects.create_user(
            user_name="testuser1",
            email="test1@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User1",
            is_active=True,
        )

        self.user2 = CustomUser.objects.create_user(
            user_name="testuser2",
            email="test2@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User2",
            is_active=True,
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

        self.premium_plan = SubscriptionPlan.objects.create(
            name="Premium",
            description="Premium plan",
            price=9.99,
            max_characters=1000,
            max_conversations=10,
            is_active=True,
        )

        self.user1_subscription = UserSubscription.objects.create(
            user=self.user1,
            plan=self.free_plan,
        )

        self.user2_subscription = UserSubscription.objects.create(
            user=self.user2,
            plan=self.premium_plan,
        )

        self.conversation = Conversation.objects.create(
            title="Test Conversation",
            owner=self.user1,
        )
        self.conversation.members.add(self.user1, self.user2)

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

    @patch("subscriptions.services.check_conversation_limits")
    def test_create_conversation(self, mock_check_limits):
        """Test creating a conversation"""
        # Mock check_conversation_limits to return (allowed, remaining)
        mock_check_limits.return_value = (True, 2)

        query = """
        mutation {
          createConversation(title: "New Test Conversation") {
            conversation {
              id
              title
              members {
                userName
              }
            }
            alert
          }
        }
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL mutation returned errors")
        self.assertIn("data", result)
        self.assertIn("createConversation", result["data"])

        conv_data = result["data"]["createConversation"]["conversation"]
        self.assertEqual(conv_data["title"], "New Test Conversation")

        members = [member["userName"] for member in conv_data["members"]]
        self.assertIn("testuser1", members)

        conversation_exists = Conversation.objects.filter(
            title="New Test Conversation", owner=self.user1
        ).exists()
        self.assertTrue(conversation_exists)

    @patch("subscriptions.services.check_conversation_limits")
    def test_create_conversation_with_members(self, mock_check_limits):
        """Test creating a conversation with additional members"""
        mock_check_limits.return_value = (True, 2)

        query = f"""
        mutation {{
          createConversation(
            title: "Group Conversation", 
            memberIds: ["{self.user2.id}"]
          ) {{
            conversation {{
              title
              members {{
                userName
              }}
            }}
          }}
        }}
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL mutation returned errors")

        conv_data = result["data"]["createConversation"]["conversation"]
        members = [member["userName"] for member in conv_data["members"]]

        self.assertIn("testuser1", members)
        self.assertIn("testuser2", members)
        self.assertEqual(len(members), 2)

    @patch("subscriptions.services.check_conversation_limits")
    def test_create_conversation_limit_reached(self, mock_check_limits):
        """Test creating a conversation when the limit is reached"""
        mock_check_limits.return_value = (False, 0)

        query = """
        mutation {
        createConversation(title: "Should Fail") {
            conversation {
            title
            }
            alert
        }
        }
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("createConversation", result["data"])
        self.assertIn(
            "you have only one conversation remaining",
            result["data"]["createConversation"]["alert"].lower(),
        )

    @patch("subscriptions.services.check_message_limits")
    def test_send_message(self, mock_check_limits):
        """Test sending a message in a conversation"""
        mock_check_limits.return_value = (True, 100)

        query = f"""
        mutation {{
          sendMessage(
            conversationId: "{self.conversation.id}",
            text: "Hello, this is a test message!"
          ) {{
            message {{
              text
              sender {{
                userName
              }}
              conversation {{
                title
              }}
            }}
          }}
        }}
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL mutation returned errors")

        message_data = result["data"]["sendMessage"]["message"]
        self.assertEqual(message_data["text"], "Hello, this is a test message!")
        self.assertEqual(message_data["sender"]["userName"], "testuser1")

        message_exists = Message.objects.filter(
            text="Hello, this is a test message!",
            sender=self.user1,
            conversation=self.conversation,
        ).exists()
        self.assertTrue(message_exists)

    @patch("subscriptions.services.check_message_limits")
    def test_send_message_limit_exceeded(self, mock_check_limits):
        """Test sending a message that exceeds character limit"""
        mock_check_limits.return_value = (False, 0)

        query = f"""
        mutation {{
          sendMessage(
            conversationId: "{self.conversation.id}",
            text: "This message is too long for the user's subscription plan"
          ) {{
            message {{
              text
            }}
          }}
        }}
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        error_msg = result["data"]["sendMessage"]["message"]["text"]
        self.assertIn("This message is too long", error_msg)

    def test_delete_conversation_as_owner(self):
        """Test deleting a conversation as the owner"""
        query = f"""
        mutation {{
          deleteConversation(conversationId: "{self.conversation.id}") {{
            success
            message
          }}
        }}
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL mutation returned errors")

        delete_data = result["data"]["deleteConversation"]
        self.assertTrue(delete_data["success"])
        self.assertIn("deleted successfully", delete_data["message"])

        conversation_exists = Conversation.objects.filter(
            id=self.conversation.id
        ).exists()
        self.assertFalse(conversation_exists)
