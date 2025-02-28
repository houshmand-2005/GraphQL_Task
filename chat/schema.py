"""
Define the schema for the chat app.
"""

import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from graphene_django import DjangoObjectType
from graphql import GraphQLError

from chat.models import Conversation, Message
from subscriptions.services import check_conversation_limits, check_message_limits
from utils.jwt_utils import get_authenticated_user

User = get_user_model()


class ConversationType(DjangoObjectType):
    """
    ConversationType is the GraphQL type for the Conversation model.
    """

    class Meta:  # pylint: disable=too-few-public-methods,missing-class-docstring
        model = Conversation


class MessageType(DjangoObjectType):
    """
    MessageType is the GraphQL type for the Message model.
    """

    class Meta:  # pylint: disable=too-few-public-methods,missing-class-docstring
        model = Message


class Query(graphene.ObjectType):
    """
    Query class for the chat app.
    """

    conversations = graphene.List(ConversationType)
    conversation = graphene.Field(ConversationType, id=graphene.ID(required=True))
    messages = graphene.List(MessageType, conversation_id=graphene.ID(required=True))

    def resolve_conversations(self, info):
        """
        Get all conversations for the authenticated user.
        """
        user = get_authenticated_user(info)
        return Conversation.objects.filter(members=user)

    def resolve_conversation(self, info, id):
        """
        Get a conversation by ID for the authenticated user
        """
        user = get_authenticated_user(info)

        try:
            conversation = Conversation.objects.get(id=id)
            if user not in conversation.members.all():
                raise GraphQLError("Access denied")
            return conversation
        except ObjectDoesNotExist as exc:
            raise GraphQLError("Conversation not found") from exc

    def resolve_messages(self, info, conversation_id):
        """
        Get all messages for a conversation.
        """
        user = get_authenticated_user(info)

        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if user not in conversation.members.all():
                raise GraphQLError("Access denied")
            return Message.objects.filter(conversation=conversation).order_by(
                "created_at"
            )
        except ObjectDoesNotExist as exc:
            raise GraphQLError("Conversation not found") from exc


class CreateConversation(graphene.Mutation):
    """
    Mutation for creating a conversation
    """

    conversation = graphene.Field(ConversationType)
    alert = graphene.String()

    class Arguments:  # pylint: disable=too-few-public-methods,missing-class-docstring
        title = graphene.String(required=True)
        member_ids = graphene.List(graphene.ID)

    def mutate(self, info, title, member_ids=None):
        """
        Create a new conversation.
        """

        user = get_authenticated_user(info)

        allowed, remaining = check_conversation_limits(user)
        if not allowed:
            raise GraphQLError(
                f"You have reached your maximum conversation limit. "
                f"Your plan allows {user.subscription.plan.max_conversations} conversations."
            )
        conversation = Conversation.objects.create(title=title, owner=user)
        conversation.members.add(user)

        if member_ids:
            for member_id in member_ids:
                try:
                    member = User.objects.get(id=member_id)
                    conversation.members.add(member)
                except User.DoesNotExist:
                    pass
        alert_message = None
        if remaining == 1:
            alert_message = "Warning: You have only one conversation remaining."
        if remaining == 0:
            alert_message = "Warning: You have reached your conversation limit."
        return CreateConversation(conversation=conversation, alert=alert_message)


class SendMessage(graphene.Mutation):
    """
    Mutation for sending a message in a conversation.
    """

    message = graphene.Field(MessageType)

    class Arguments:  # pylint: disable=too-few-public-methods,missing-class-docstring
        conversation_id = graphene.ID(required=True)
        text = graphene.String(required=True)

    def mutate(self, info, conversation_id, text):
        """
        Send a message in a conversation.
        """
        user = get_authenticated_user(info)

        message_length = len(text)
        allowed, _ = check_message_limits(user, message_length)
        if not allowed:
            raise GraphQLError(
                f"Your message exceeds your character limit. "
                f"out of {user.subscription.plan.max_characters}."
            )
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if user not in conversation.members.all():
                raise GraphQLError("Access denied")

            message = Message.objects.create(
                conversation=conversation, sender=user, text=text
            )

            return SendMessage(message=message)
        except ObjectDoesNotExist as exc:
            raise GraphQLError("Conversation not found") from exc


class DeleteConversation(graphene.Mutation):
    """
    Mutation for deleting a conversation.
    Only the owner of the conversation can delete it.
    """

    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:  # pylint: disable=too-few-public-methods,missing-class-docstring
        conversation_id = graphene.ID(required=True)

    def mutate(self, info, conversation_id):
        """
        Delete a conversation.
        """

        user = get_authenticated_user(info)

        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if conversation.owner != user:
                raise GraphQLError(
                    "Permission denied: Only the owner can delete this conversation"
                )

            conversation.delete()

            return DeleteConversation(
                success=True, message="Conversation deleted successfully"
            )

        except ObjectDoesNotExist as exc:
            raise GraphQLError("Conversation not found") from exc


class AddUserToConversation(graphene.Mutation):
    """
    Mutation for adding a user to an existing conversation.
    Only the owner of the conversation can add users.
    """

    success = graphene.Boolean()
    message = graphene.String()
    conversation = graphene.Field(ConversationType)

    class Arguments:  # pylint: disable=too-few-public-methods,missing-class-docstring
        conversation_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)

    def mutate(self, info, conversation_id, user_id):
        """
        Add a user to a conversation.
        """
        current_user = get_authenticated_user(info)

        try:
            conversation = Conversation.objects.get(id=conversation_id)

            if conversation.owner != current_user:
                raise GraphQLError(
                    "Permission denied: Only the owner can add users to this conversation"
                )

            try:
                user_to_add = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return AddUserToConversation(
                    success=False, message="User not found", conversation=conversation
                )

            if user_to_add in conversation.members.all():
                return AddUserToConversation(
                    success=False,
                    message="User is already a member of this conversation",
                    conversation=conversation,
                )

            conversation.members.add(user_to_add)

            return AddUserToConversation(
                success=True,
                message="User has been added to the conversation",
                conversation=conversation,
            )

        except ObjectDoesNotExist as exc:
            raise GraphQLError("Conversation not found") from exc


class Mutation(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """
    Define mutations for the chat app
    """

    create_conversation = CreateConversation.Field()
    send_message = SendMessage.Field()
    delete_conversation = DeleteConversation.Field()
    add_user_to_conversation = AddUserToConversation.Field(
        description="Add a user to an existing conversation (owner only)"
    )
