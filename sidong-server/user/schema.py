from django.contrib.auth.models import User
from django.db import transaction

from graphene_file_upload.scalars import Upload
from graphene import Mutation, ObjectType, String, Boolean, Field, List, Int, ID
from graphene_django.types import DjangoObjectType
from user.models import Artist
from file.models import File, create_file, validate_file


class UserType(DjangoObjectType):
    class Meta:
        model = User


class ArtistType(DjangoObjectType):
    class Meta:
        model = Artist


class Query(ObjectType):
    user = Field(UserType, id=ID(), email=String())
    current_user = Field(UserType)
    artists = List(ArtistType, last_artist_id=ID(), page_size=Int())

    def resolve_user(self, info, id=None, email=None):
        if id is not None:
            return User.objects.get(id=id)
        if email is not None:
            return User.objects.get(username=email)
        return None

    def resolve_current_user(self, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        return user

    def resolve_artists(self, info, last_artist_id=None, page_size=12):
        artists_filter = {'id__lt': last_artist_id}

        if last_artist_id is None:
            last_artist_id = Artist.objects.last().id
            artists_filter = {'id__lte': last_artist_id}

        return Artist.objects.filter(
            **artists_filter,
        ).order_by('-id')[:page_size]


class CreateUser(Mutation):
    class Arguments:
        email = String(required=True)
        password = String(required=True)

    success = Boolean()

    def mutate(self, info, email, password):
        if User.objects.filter(username=email).exists():
            return CreateUser(success=False)
        else:
            User.objects.create_user(username=email, password=password)
            return CreateUser(success=True)


class CreateArtist(Mutation):
    class Arguments:
        artist_name = String(required=True)
        real_name = String(required=True)
        phone = String(required=True)
        description = String(required=True)
        category = Int(required=True)
        residence = Int(required=True)
        thumbnail = Upload(required=True)
        representative_work = Upload(required=True)

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, artist_name, real_name,
               phone, description, category, residence, thumbnail, representative_work):
        current_user = info.context.user

        validate_thumbnail = validate_file(thumbnail[0], File.BUCKET_ASSETS)
        if validate_thumbnail['status'] == 'fail':
            return CreateArtist(success=False, msg=validate_thumbnail['msg'])

        validate_representative_work = validate_file(
            representative_work[0], File.BUCKET_ASSETS)
        if validate_representative_work['status'] == 'fail':
            return CreateArtist(success=False, msg=validate_representative_work['msg'])

        thumbnail_file = create_file(
            thumbnail[0], File.BUCKET_ASSETS, current_user)
        if thumbnail_file['status'] == 'fail':
            return CreateArtist(success=False, msg=thumbnail_file['msg'])

        representative_work_file = create_file(
            representative_work[0], File.BUCKET_ASSETS, current_user)
        if representative_work_file['status'] == 'fail':
            return CreateArtist(success=False, msg=representative_work_file['msg'])

        Artist.objects.create(
            user=current_user,
            artist_name=artist_name,
            real_name=real_name,
            phone=phone,
            description=description,
            category=category,
            residence=residence,
            thumbnail=thumbnail_file['instance'],
            representative_work=representative_work_file['instance'],
        )

        return CreateArtist(success=True)


class Mutation(ObjectType):
    create_user = CreateUser.Field()
    create_artist = CreateArtist.Field()
