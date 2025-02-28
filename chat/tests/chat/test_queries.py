"""
Test GraphQL queries for the chat app.
"""

from unittest.mock import Mock

from django.test import TestCase
from graphene.test import Client

from chat.models import Conversation, Message
from core.schema import schema
from users.models import CustomUser
from utils.jwt_utils import generate_access_token


class ChatQueriesTest(TestCase):  # pylint: disable=too-many-instance-attributes
    """
    Test GraphQL queries for the chat app.
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

        self.non_member = CustomUser.objects.create_user(
            user_name="nonmember",
            email="nonmember@example.com",
            password="testpassword123",
            first_name="Non",
            last_name="Member",
            is_active=True,
        )

        self.conversation1 = Conversation.objects.create(
            title="First Conversation",
            owner=self.user1,
        )
        self.conversation1.members.add(self.user1, self.user2)

        self.conversation2 = Conversation.objects.create(
            title="Second Conversation",
            owner=self.user1,
        )
        self.conversation2.members.add(self.user1)

        self.conversation3 = Conversation.objects.create(
            title="Third Conversation",
            owner=self.user2,
        )
        self.conversation3.members.add(self.user2)

        self.message1 = Message.objects.create(
            conversation=self.conversation1,
            sender=self.user1,
            text="Hello from user1",
        )

        self.message2 = Message.objects.create(
            conversation=self.conversation1,
            sender=self.user2,
            text="Hello from user2",
        )

        self.message3 = Message.objects.create(
            conversation=self.conversation1,
            sender=self.user1,
            text="How are you doing?",
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

    def test_get_conversations_authenticated(self):
        """Test retrieving conversations for an authenticated user"""
        query = """
        query {
          conversations {
            id
            title
            owner {
              userName
            }
            members {
              userName
            }
          }
        }
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL query returned errors")
        self.assertIn("data", result)
        self.assertIn("conversations", result["data"])

        conversations = result["data"]["conversations"]

        # User1 should see 2 conversations (conversation1 and conversation2)
        self.assertEqual(len(conversations), 2)

    def test_get_conversation_by_id(self):
        """Test retrieving a specific conversation by ID"""
        query = f"""
        query {{
          conversation(id: "{self.conversation1.id}") {{
            title
            owner {{
              userName
            }}
            members {{
              userName
            }}
          }}
        }}
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)
        self.assertNotIn("errors", result, "GraphQL query returned errors")
        self.assertIn("data", result)
        self.assertIn("conversation", result["data"])

        conversation = result["data"]["conversation"]
        self.assertEqual(conversation["title"], "First Conversation")

        self.assertEqual(conversation["owner"]["userName"], "testuser1")

    def test_get_nonexistent_conversation(self):
        """Test retrieving a conversation that doesn't exist"""
        query = """
        query {
          conversation(id: "999") {
            title
          }
        }
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("errors", result)
        error_msg = result["errors"][0]["message"]
        self.assertIn("Conversation not found", error_msg)

    def test_get_messages_for_conversation(self):
        """Test retrieving messages for a specific conversation"""
        query = f"""
        query {{
          messages(conversationId: "{self.conversation1.id}") {{
            text
            sender {{
              userName
            }}
          }}
        }}
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertNotIn("errors", result, "GraphQL query returned errors")
        self.assertIn("data", result)
        self.assertIn("messages", result["data"])

        messages = result["data"]["messages"]

        self.assertEqual(len(messages), 3)

    def test_get_messages_nonmember(self):
        """Test retrieving messages as a non-member of conversation (should fail)"""
        query = f"""
        query {{
          messages(conversationId: "{self.conversation1.id}") {{
            text
          }}
        }}
        """

        context_value = self._create_mock_context(self.non_member)
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("errors", result)
        error_msg = result["errors"][0]["message"]
        self.assertIn("Access denied", error_msg)

    def test_get_messages_nonexistent_conversation(self):
        """Test retrieving messages for a conversation that doesn't exist"""
        query = """
        query {
          messages(conversationId: "999") {
            text
          }
        }
        """

        context_value = self._create_mock_context(self.user1)
        result = self.client.execute(query, context_value=context_value)

        self.assertIn("errors", result)
        error_msg = result["errors"][0]["message"]
        self.assertIn("Conversation not found", error_msg)
