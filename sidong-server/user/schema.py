from django.contrib.auth.models import User
from django.db import transaction

from graphene_file_upload.scalars import Upload
from graphene import Mutation, ObjectType, String, Boolean, \
    Field, List, Int, ID
from graphene_django.types import DjangoObjectType
from user.models import Artist, UserInfo, Order, Like as ArtistLike
from art.models import Art, Like as ArtLike
from file.models import File, create_file, validate_file


class UserInfoType(DjangoObjectType):
    class Meta:
        model = UserInfo


class UserType(DjangoObjectType):
    class Meta:
        model = User

    liking_arts_count = Int()
    liking_artists_count = Int()
    last_userinfo = Field(UserInfoType)

    def resolve_liking_arts_count(self, info):
        return ArtLike.objects.filter(user_id=self.id).count()

    def resolve_liking_artists_count(self, info):
        return ArtistLike.objects.filter(user_id=self.id).count()

    def resolve_last_userinfo(self, info):
        return UserInfo.objects.filter(user_id=self.id).last()


class ArtistType(DjangoObjectType):
    class Meta:
        model = Artist
        convert_choices_to_enum = False

    current_user_likes_this_artist = Boolean()

    def resolve_current_user_likes_this_artist(self, info):
        user = info.context.user
        if user.is_anonymous:
            return False
        return ArtistLike.objects.filter(user=user, artist_id=self.id).exists()


class OrderType(DjangoObjectType):
    class Meta:
        model = Order


class ArtistLikeType(ObjectType):
    id = ID()
    last_like_id = ID()
    artists = List(ArtistType)


class OrderConnection(ObjectType):
    orders = List(OrderType)
    total_count = Int()


class Query(ObjectType):
    user = Field(UserType, id=ID(), email=String())
    current_user = Field(UserType)
    artist = Field(ArtistType, artist_id=ID())
    artists = List(ArtistType, page=Int(), page_size=Int(),
                   category=String(), residence=String(),
                   ordering_priority=List(String))
    user_liking_artists = Field(ArtistLikeType, user_id=ID(required=True),
                                last_like_id=ID())
    orders = Field(OrderConnection, page=Int(), page_size=Int())

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

    def resolve_artist(self, info, artist_id):
        return Artist.objects.get(id=artist_id)

    def resolve_artists(self, info, page=0, page_size=20, category=None,
                        residence=None, ordering_priority=None):

        artists_filter = {}

        if category:  # 필터 적용
            if category != 'all':
                artists_filter['category'] = category
            if residence != 'all':
                artists_filter['residence'] = residence

        artists = Artist.objects.filter(
            is_approved=True, **artists_filter)

        if not artists:
            return None

        if ordering_priority is None:
            ordering_priority = ['-id']

        return artists.order_by(
            *ordering_priority)[page*page_size:(page + 1)*page_size]

    def resolve_user_liking_artists(self, info, user_id, last_like_id=None):
        like_instances = ArtistLike.objects.filter(
            user=User.objects.get(id=user_id)).order_by('-id')

        if not like_instances:
            return None

        like_filter = {}
        if last_like_id:
            like_filter = {'id__lt': last_like_id}

        like_instances = like_instances.filter(
            **like_filter)[:20]

        return {
            'id': user_id,
            'last_like_id': like_instances[len(like_instances) - 1].id if like_instances else None,
            'artists': [like.artist for like in like_instances],
        }

    def resolve_orders(self, info, page=0, page_size=10):
        user = info.context.user
        if user.is_anonymous:
            return None

        orders = Order.objects.filter(userinfo__user=user)

        return {
            'orders': orders.order_by('-id')[page*page_size:(page + 1)*page_size],
            'total_count': orders.count(),
        }


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
        website = String()

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, artist_name, real_name, website,
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
            website=website if website else None,
        )

        return CreateArtist(success=True)


class LikeArtist(Mutation):
    class Arguments:
        artist_id = ID(required=True)

    success = Boolean()

    def mutate(self, info, artist_id):
        user = info.context.user
        if user.is_anonymous:
            return LikeArtist(success=False)

        artist = Artist.objects.get(id=artist_id)
        ArtistLike.objects.create(user=user, artist=artist)
        artist.like_count += 1
        artist.save()

        return LikeArtist(success=True)


class CancelLikeArtist(Mutation):
    class Arguments:
        artist_id = ID(required=True)

    success = Boolean()

    def mutate(self, info, artist_id):
        user = info.context.user
        if user.is_anonymous:
            return CancelLikeArtist(success=False)

        artist = Artist.objects.get(id=artist_id)
        like = ArtistLike.objects.filter(user=user, artist=artist)
        like.delete()

        if artist.like_count > 0:
            artist.like_count -= 1
            artist.save()

        return CancelLikeArtist(success=True)


class CreateOrder(Mutation):
    class Arguments:
        art_id = ID(required=True)
        checked_save = Boolean(required=True)
        address = String(required=True)
        name = String(required=True)
        phone = String(required=True)

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, art_id, checked_save, address, name, phone):
        user = info.context.user
        if user.is_anonymous:
            return CreateOrder(success=False, msg="로그인이 필요합니다.")

        art = Art.objects.get(id=art_id)
        userinfo, _ = UserInfo.objects.get_or_create(
            user=user,
            defaults={
                'name': name,
                'phone': phone,
                'address': address,
            },
        )

        if checked_save:
            userinfo = UserInfo.objects.create(
                user=user,
                name=name,
                phone=phone,
                address=address,
            )

        Order.objects.create(
            userinfo=userinfo,
            art_name=art.name,
            price=art.price,
            art=art,
            artist=art.artist,
        )

        return CreateOrder(success=True)


class Mutation(ObjectType):
    create_user = CreateUser.Field()
    create_artist = CreateArtist.Field()
    like_artist = LikeArtist.Field()
    cancel_like_artist = CancelLikeArtist.Field()
    create_order = CreateOrder.Field()
