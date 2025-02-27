import datetime

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from graphql import GraphQLError

User = get_user_model()

JWT_ACCESS_TOKEN_EXPIRATION_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRATION_DAYS = 7


# TODO: Add plan to token!
def generate_access_token(user):
    """Generate JWT access token for a user"""
    payload = {
        "user_id": str(user.id),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRATION_MINUTES),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user):
    """Generate JWT refresh token for a user"""
    payload = {
        "user_id": str(user.id),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=JWT_REFRESH_TOKEN_EXPIRATION_DAYS),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "refresh": True,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def get_authenticated_user(info):
    """Get authenticated user from request or raise GraphQLError"""
    request = info.context
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")

    if not auth_header.startswith("Bearer "):
        raise GraphQLError("Authentication required")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("refresh"):
            raise GraphQLError("Cannot use refresh token for authentication")
        user_id = payload.get("user_id")
        try:
            return User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError) as exc:
            raise GraphQLError("User not found") from exc
    except jwt.ExpiredSignatureError as exc:
        raise GraphQLError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise GraphQLError("Invalid token") from exc
