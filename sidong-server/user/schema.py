from django.contrib.auth.models import User
from django.db import transaction

from graphene_file_upload.scalars import Upload
from graphene import Mutation, ObjectType, String, Boolean, \
    Field, List, Int, ID
from graphene_django.types import DjangoObjectType
from user.models import Artist, UserInfo, Order, Like as ArtistLike
from art.models import Art, Like as ArtLike
from file.models import File, create_file, validate_file
from django.utils import timezone


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
        convert_choices_to_enum = False

    delivery_company = String()
    delivery_number = String()

    def resolve_created_at(self, info):
        return timezone.localdate(self.created_at)

    def resolve_delivery_company(self, info):
        return self.delivery_data['delivery_company'] if self.delivery_data else None

    def resolve_delivery_number(self, info):
        return self.delivery_data['delivery_number'] if self.delivery_data else None


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
    artist = Field(ArtistType, artist_id=ID(required=True))
    order = Field(OrderType, order_id=ID(required=True))
    artists = List(ArtistType, page=Int(), page_size=Int(),
                   category=String(), residence=String(),
                   ordering_priority=List(String))
    user_liking_artists = Field(ArtistLikeType, user_id=ID(required=True),
                                last_like_id=ID())
    orders = Field(OrderConnection, page=Int(), page_size=Int())
    sales = Field(OrderConnection, page=Int(), page_size=Int())

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

    def resolve_order(self, info, order_id):
        order = Order.objects.get(id=order_id)
        current_user_id = info.context.user.id

        if order.userinfo.user.id != current_user_id:
            if order.artist.user.id != current_user_id:
                return None

        return order

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

    def resolve_sales(self, info, page=0, page_size=10):
        user = info.context.user
        if user.is_anonymous:
            return None

        artist = Artist.objects.get(user=user)
        sales = Order.objects.filter(artist=artist)

        return {
            'orders': sales.order_by('-id')[page*page_size:(page + 1)*page_size],
            'total_count': sales.count(),
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
        address = String(required=True)
        name = String(required=True)
        phone = String(required=True)
        recipient_address = String(required=True)
        recipient_name = String(required=True)
        recipient_phone = String(required=True)

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, art_id, recipient_address, address,
               recipient_name, name, recipient_phone, phone):
        user = info.context.user
        if user.is_anonymous:
            return CreateOrder(success=False, msg="로그인이 필요합니다.")

        art = Art.objects.get(id=art_id)

        if art.sale_status != Art.ON_SALE:
            return CreateOrder(success=False, msg="판매 중인 작품이 아닙니다.")

        userinfo, _ = UserInfo.objects.update_or_create(
            user=user,
            defaults={
                'name': name,
                'phone': phone,
                'address': address,
            },
        )

        Order.objects.create(
            userinfo=userinfo,
            art_name=art.name,
            price=art.price,
            art=art,
            artist=art.artist,
            recipient_address=recipient_address,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
        )

        art.sale_status = Art.SOLD_OUT
        art.save()
        # SMS 전송
        # 주문/결제 정보 메세지
        # TO: 주문자, 작가
        return CreateOrder(success=True)


class CancelOrder(Mutation):
    class Arguments:
        order_id = ID(required=True)

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, order_id):
        order = Order.objects.get(id=order_id)

        if info.context.user.id != order.userinfo.user.id:
            return CancelOrder(success=False, msg="주문을 취소할 권한이 없습니다.")

        order.status = Order.CANCEL
        order.save()

        order.art.sale_status = Art.ON_SALE
        order.art.save()
        # SMS 전송
        # 주문 취소 안내 메세지
        # TO: 작가
        return CancelOrder(success=True)


class CompleteOrder(Mutation):
    class Arguments:
        order_id = ID(required=True)

    success = Boolean()
    msg = String()

    def mutate(self, info, order_id):
        order = Order.objects.get(id=order_id)

        if info.context.user.id != order.userinfo.user.id:
            return CompleteOrder(success=False, msg="구매 완료할 권한이 없습니다.")

        order.status = Order.COMPLETED
        order.save()
        # SMS 전송
        # 구매 완료 안내 메세지
        # TO: 작가
        return CompleteOrder(success=True)


class UpdateOrder(Mutation):
    class Arguments:
        order_id = ID(required=True)
        status = Int(required=True)
        delivery_company = String()
        delivery_number = String()

    success = Boolean()
    msg = String()

    def mutate(self, info, order_id, delivery_company, delivery_number, status):
        order = Order.objects.get(id=order_id)

        if info.context.user.id != order.artist.user.id:
            return UpdateOrder(success=False, msg="주문을 수정할 권한이 없습니다.")

        if order.status == Order.CANCEL:
            return UpdateOrder(success=False, msg="이미 취소된 주문입니다.")

        if order.status <= Order.FAIL:
            return UpdateOrder(success=False, msg="아직 결제가 왼료되지 않았습니다.")

        if status == Order.ON_DELIVERY or status == Order.DELIVERY_COMPLETED:
            if delivery_company and delivery_number:
                order.delivery_data = {
                    'delivery_company': delivery_company,
                    'delivery_number': delivery_number,
                }
            else:
                return UpdateOrder(success=False, msg="택배 회사명과 송장 번호를 입력해주세요.(필수)")

        # SMS 전송
        # 상태 변경 안내
        # TO: 주문자
        order.status = status
        order.save()

        return UpdateOrder(success=True)


class Mutation(ObjectType):
    create_user = CreateUser.Field()
    create_artist = CreateArtist.Field()
    like_artist = LikeArtist.Field()
    cancel_like_artist = CancelLikeArtist.Field()
    create_order = CreateOrder.Field()
    cancel_order = CancelOrder.Field()
    update_order = UpdateOrder.Field()
    complete_order = CompleteOrder.Field()
