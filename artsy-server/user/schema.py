from graphene import Mutation, ObjectType, String, Boolean, Field, List, Int, DateTime

from django.contrib.auth.models import User
from graphene_django.types import DjangoObjectType


class UserType(DjangoObjectType):
    class Meta:
        model = User


class CreateUser(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)

    user = Field(UserType)
    status = Boolean()
    msg = String()

    def mutate(self, info, email, password):
        if User.objects.filter(username=email).exists():
            status = False
            msg = "이미 등록된 이메일입니다."
            return CreateUser(status=status, msg=msg)
        else:
            user = User.objects.create_user(username=email, password=password)
            status = True
            return CreateUser(user=user, status=status)


class LoginUser(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)

    user = Field(UserType)
    status = Boolean()
    msg = String()

    def mutate(self, info, email, password):
        from django.contrib.auth import authenticate, login

        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            status = True
            return LoginUser(user=user, status=status)
        else:
            status = False
            msg = "로그인에 실패했습니다."
            return LoginUser(status=status, msg=msg)


class Mutation(ObjectType):
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()


class Query(object):
    user = Field(UserType, id=Int(), email=String())
    all_users = List(UserType)
    current_user = Field(UserType)

    def resolve_user(self, info, id, email):
        if id is not None:
            return User.objects.get(id=id)

        if email is not None:
            return User.objects.get(username=email)

        return None

    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()

    def resolve_current_user(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Not logged in")

        return user
