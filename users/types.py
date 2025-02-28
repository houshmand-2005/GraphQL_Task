"""
This module contains the GraphQL types for the User model.
"""

import graphene
from django.contrib.auth import get_user_model

from graphene_django import DjangoObjectType


User = get_user_model()


class UserType(DjangoObjectType):
    """
    UserType is the GraphQL type for the User model.
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """We specify the model and the fields for the UserType."""

        model = User
        exclude = ("password",)


class TokenType(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """
    TokenType is the GraphQL type for the access and refresh

    access: JWT access token
    refresh: JWT refresh token
    """

    access = graphene.String()
    refresh = graphene.String()
