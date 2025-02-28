"""
This file is used to combine all the schemas from different apps into one schema.
"""

import graphene

from chat import schema as chat_schema
from subscriptions import schema as subscriptions_schema
from users import schema as users_schema


class Query(
    users_schema.Query,
    chat_schema.Query,
    subscriptions_schema.Query,
    graphene.ObjectType,
):
    """Root query for the schema"""


class Mutation(  # pylint: disable=too-few-public-methods
    users_schema.Mutation,
    chat_schema.Mutation,
    subscriptions_schema.Mutation,
    graphene.ObjectType,
):
    """Root mutation for the schema"""


schema = graphene.Schema(query=Query, mutation=Mutation)
