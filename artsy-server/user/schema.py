import graphene

from django.contrib.auth.models import User
from graphene_django.types import DjangoObjectType


class UserType(DjangoObjectType):
    class Meta:
        model = User


class UserMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)

    def mutate(self, info, email, password):
        user = User.objects.create_user(
            username=email.split("@")[0], password=password, email=email,
        )
        return UserMutation(user=user)


class Mutation(graphene.ObjectType):
    create_user = UserMutation.Field()


class Query(object):
    user = graphene.Field(
        UserType,
        id=graphene.Int(),
        username=graphene.String(),
        email=graphene.String(),
        date_joined=graphene.DateTime(),
    )
    all_users = graphene.List(UserType)

    def resolve_user(self, info, **kwargs):
        id = kwargs.get("id")
        username = kwargs.get("username")
        email = kwargs.get("email")

        if id is not None:
            return User.objects.get(id=id)

        if username is not None:
            return User.objects.get(username=username)

        if email is not None:
            return User.objects.get(email=email)

        return None

    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()
