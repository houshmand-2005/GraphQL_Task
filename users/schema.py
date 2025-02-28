"""
This file provides the schema for the users app.
"""

import uuid

import graphene
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from graphql import GraphQLError

from users.models import EmailVerificationToken
from users.services import create_user
from users.types import TokenType, UserType
from utils.jwt_utils import (
    decode_token,
    generate_access_token,
    generate_refresh_token,
    get_authenticated_user,
    get_user_from_payload,
)
from utils.validators import username_validator

User = get_user_model()


class Query(graphene.ObjectType):
    """
    Query class for the users app.

    me: Get the authenticated user.
    users: Get all users (only for staff users).
    """

    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    def resolve_me(self, info):
        """
        Get the authenticated user Base on JWT token.
        """
        user = get_authenticated_user(info)
        return user

    def resolve_users(self, info):
        """
        List all users (only for staff users).
        """
        user = get_authenticated_user(info)
        if not user.is_staff:
            raise GraphQLError("Permission denied")
        return User.objects.all()


class LoginUser(graphene.Mutation):
    """
    LoginUser is the mutation to authenticate a user.
    """

    token = graphene.Field(TokenType)
    user = graphene.Field(UserType)

    class Arguments:  # pylint: disable=too-few-public-methods
        """
        Required arguments for the LoginUser mutation.
        """

        username = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, username, password):  # pylint: disable=unused-argument, too-many-arguments
        """
        Check if the user exists and the password is correct.
        """
        user = authenticate(username=username, password=password)

        if not user:
            raise GraphQLError("Invalid credentials")

        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        return LoginUser(
            token=TokenType(access=access_token, refresh=refresh_token), user=user
        )


class RefreshToken(graphene.Mutation):
    """
    RefreshToken is the mutation to refresh the access token.
    """

    access = graphene.String()

    class Arguments:  # pylint: disable=too-few-public-methods
        """
        Required arguments for the RefreshToken mutation.
        """

        refresh_token = graphene.String(required=True)

    def mutate(self, info, refresh_token):  # pylint: disable=unused-argument
        """
        Check if the refresh token is valid and generate a new access token.
        """
        payload = decode_token(refresh_token)

        if not payload.get("refresh"):
            raise GraphQLError("Invalid token type: not a refresh token")

        user = get_user_from_payload(payload)

        new_access_token = generate_access_token(user)
        return RefreshToken(access=new_access_token)


class CreateUser(graphene.Mutation):
    """
    CreateUser is the mutation to register a new user.
    The user will be inactive until email verification.

    """

    user = graphene.Field(UserType)

    class Arguments:  # pylint: disable=too-few-public-methods
        """
        Required arguments for the CreateUser mutation.
        """

        user_name = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)

    def mutate(self, info, user_name, email, password, first_name, last_name):  # pylint: disable=unused-argument, too-many-arguments
        """
        Check if the user exists and create a new user.
        """
        if len(user_name) < 5:
            raise GraphQLError("Username must be at least 5 characters long")
        try:
            username_validator(user_name)
        except ValidationError as exc:
            raise GraphQLError(str(exc)) from exc

        if User.objects.filter(user_name=user_name).exists():
            raise GraphQLError("Username already exists")

        if User.objects.filter(email=email).exists():
            raise GraphQLError("Email already exists")
        try:
            validate_email(email)
        except ValidationError as exc:
            raise GraphQLError("Invalid email format") from exc

        user = create_user(
            user_name=user_name,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return CreateUser(user=user)


class VerifyEmail(graphene.Mutation):
    """
    Verify email using the token sent to the user's email.
    """

    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.Field(TokenType)

    class Arguments:  # pylint: disable=too-few-public-methods
        """
        Required arguments for the VerifyEmail mutation.
        """

        token = graphene.String(required=True)

    def mutate(self, info, token):  # pylint: disable=unused-argument
        """
        Verify the email using the token.
        """
        try:
            token_uuid = uuid.UUID(token)
            verification_token = EmailVerificationToken.objects.get(token=token_uuid)
            if not verification_token.is_valid():
                return VerifyEmail(
                    success=False,
                    message="Verification link has expired or already used",
                )

            user = verification_token.user
            user.is_active = True
            user.save()
            verification_token.is_used = True
            verification_token.save()

            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)

            return VerifyEmail(
                success=True,
                message="Your email has been verified successfully!",
                token=TokenType(access=access_token, refresh=refresh_token),
            )

        except (ValueError, ObjectDoesNotExist):
            return VerifyEmail(success=False, message="Invalid verification token")


class Mutation(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """
    Mutation class for the users app.
    """

    login = LoginUser.Field()
    refresh_token = RefreshToken.Field()
    register = CreateUser.Field()
    verify_email = VerifyEmail.Field()
