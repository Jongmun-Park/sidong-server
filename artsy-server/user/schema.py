import graphene

from django.contrib.auth.models import User
from graphene_django.types import DjangoObjectType


class UserType(DjangoObjectType):
    class Meta:
        model = User


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
		email= kwargs.get("email")

		if id is not None:
			return User.objects.get(id=id)

		if username is not None:
			return User.objects.get(username=username)

		if email is not None:
			return User.objects.get(email=email)

		return None

	def resolve_all_users(self, info, **kwargs):
		return User.objects.all()
