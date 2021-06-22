from graphene import ObjectType, Schema, Int, Field, Boolean, String
import graphql_jwt
import art.schema
import file.schema
import user.schema
from django.db.models import Q
from user.models import Artist
from art.models import Art


class SearchResultCountConnection(ObjectType):
    result = Boolean()
    art_count = Int()
    artist_count = Int()


class SearchQuery(ObjectType):
    search_result_count = Field(
        SearchResultCountConnection, word=String(required=True))

    def resolve_search_result_count(self, info, word):
        print('word:', word)
        if not word:
            return {'result': False}

        return {
            'result': True,
            'art_count': Art.objects.filter(name__icontains=word).count(),
            'artist_count': Artist.objects.filter(
                Q(real_name__icontains=word) | Q(artist_name__icontains=word)).count(),
        }


class Query(SearchQuery,
            art.schema.Query,
            file.schema.Query,
            user.schema.Query, ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


class Mutation(art.schema.Mutation, user.schema.Mutation, ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = Schema(query=Query, mutation=Mutation)
