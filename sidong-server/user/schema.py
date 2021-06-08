from django.contrib.auth.models import User
from django.db import transaction
from graphene_file_upload.scalars import Upload
from graphene import Mutation, ObjectType, String, Boolean, \
    Field, List, Int, ID
from graphene_django.types import DjangoObjectType
from user.models import Artist, UserInfo, Order, Like as ArtistLike
from user.func import cancel_payment, create_order, create_payment, \
    update_or_create_userinfo, validate_payment, send_sms, send_lms
from art.models import Art, Like as ArtLike
from file.models import File, create_file, validate_file
from django.utils import timezone


class UserInfoType(DjangoObjectType):
    class Meta:
        model = UserInfo

    def resolve_phone(self, info):
        return '0' + str(self.phone.national_number)


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

    def resolve_phone(self, info):
        return '0' + str(self.phone.national_number)


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

    def resolve_recipient_phone(self, info):
        return '0' + str(self.recipient_phone.national_number)


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
            if User.objects.filter(id=id).exists():
                return User.objects.get(id=id)
            else:
                return None

        if email is not None:
            if User.objects.filter(username=email).exists():
                return User.objects.get(username=email)
            else:
                return None

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

        if Artist.objects.filter(user=current_user).exists():
            return CreateArtist(success=False, msg="이미 작가 신청하셨습니다.\n관리자의 승인이 필요합니다.")

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
            is_approved=True,
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
        imp_uid = String(required=True)

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, art_id, recipient_address, address,
               recipient_name, name, recipient_phone, phone, imp_uid):
        user = info.context.user
        if user.is_anonymous:
            return CreateOrder(success=False, msg="로그인이 필요합니다.")

        art = Art.objects.get(id=art_id)
        if art.sale_status != Art.ON_SALE:
            return CreateOrder(success=False, msg="판매 중인 작품이 아닙니다.")

        result_of_payment, msg_or_payment_info = validate_payment(
            imp_uid, art.price+art.delivery_fee)

        if result_of_payment is False:
            return CreateOrder(success=False, msg=msg_or_payment_info)

        userinfo = update_or_create_userinfo(user, name, phone, address)

        result_of_create_order, msg_or_order = create_order(
            art, userinfo, recipient_address, recipient_name, recipient_phone)

        if result_of_create_order is False:
            return CreateOrder(success=False, msg=msg_or_order)

        result_of_create_payment, msg = create_payment(
            msg_or_payment_info, msg_or_order)

        if result_of_create_payment is False:
            return CreateOrder(success=False, msg=msg)

        msg_or_order.status = Order.SUCCESS
        msg_or_order.save()

        art.sale_status = Art.SOLD_OUT
        art.save()

        art_name = art.name[:8] + \
            '..' if len(art.name) > 8 else art.name
        order_id = str(msg_or_order.id)

        # 고객 안내
        send_lms([{"recipientNo": phone}],
                 "[작업터] 주문 완료\n" +
                 "- 주문번호: " + order_id + "\n" +
                 "- 작품명: " + art_name + "\n" +
                 "주문에 진심으로 감사드립니다.\n" +
                 "작가분이 배송 준비할 예정입니다.\n" +
                 "안전히 배송될 수 있게 진행 상황을 문자로 안내드리겠습니다.\n" +
                 "작업터를 이용해주셔서 감사드립니다. :)"
                 )
        # 작가 안내
        send_lms([{"recipientNo": art.artist.phone.national_number}],
                 "[작업터] 작품 판매 안내\n" +
                 "- 주문번호: " + order_id + "\n" +
                 "- 작품명: " + art_name + "\n" +
                 "작품이 판매되었습니다. :)\n" +
                 "배송 준비 부탁드립니다.\n\n" +
                 "[필독 사항]\n" +
                 "* 판매 관리에서 '배송 준비중' 으로 상태 변경 부탁드립니다.\n" +
                 "* '작품보증서'를 작품과 함께 배송하셔야 합니다.\n" +
                 "* '작품보증서'는 계정 메일로 보내드리겠습니다.\n\n" +
                 "작품 판매를 축하드립니다. 안전히 작품이 구매자에게 전달될 수 있도록 꼼꼼한 포장 부탁드립니다 :)"
                 )

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

        result_of_cancel_payment, msg = cancel_payment(
            order.payments.last().id)

        if result_of_cancel_payment is False:
            return CancelOrder(success=False, msg=msg)

        order.status = Order.CANCEL
        order.save()

        order.art.sale_status = Art.ON_SALE
        order.art.save()

        art_name = order.art_name[:8] + \
            '..' if len(order.art_name) > 8 else order.art_name

        # 작가 안내
        send_sms([{"recipientNo": order.artist.phone.national_number}], """
            [작업터]\n- 작품명: {art_name}\n주문이 취소됐습니다.\n확인 바랍니다.
        """.format(art_name=art_name))

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

        art_name = order.art_name[:8] + \
            '..' if len(order.art_name) > 8 else order.art_name

        # 작가 안내
        send_lms([{"recipientNo": order.artist.phone.national_number}],
                 "[작업터] 구매 확정 안내\n\n" +
                 "- 작품명: " + art_name + "\n" +
                 "구매자가 구매를 확정했습니다. 판매 축하드립니다. :)\n\n" +
                 "[필독 사항]\n" +
                 "* 대금 정산은 매월 마지막 주에 진행됩니다.\n" +
                 "* 정산이 끝나면 다시 안내 문자 드리겠습니다.\n\n" +
                 "작업터를 이용해주셔서 항상 감사드립니다. 작가님들을 위한 서비스가 되겠습니다.(꾸벅)"
                 )

        return CompleteOrder(success=True)


class RequestRefund(Mutation):
    class Arguments:
        order_id = ID(required=True)

    success = Boolean()
    msg = String()

    def mutate(self, info, order_id):
        order = Order.objects.get(id=order_id)

        if info.context.user.id != order.userinfo.user.id:
            return RequestRefund(success=False, msg="환불 요청할 권한이 없습니다.")

        order.status = Order.REFUND
        order.save()

        art_name = order.art_name[:8] + \
            '..' if len(order.art_name) > 8 else order.art_name
        # 고객 안내
        send_sms([{"recipientNo": order.userinfo.phone.national_number}], """
            [작업터]\n- 작품명: {art_name}\n환불 요청 접수 완료.\n감사합니다.
        """.format(art_name=art_name))
        # 작가 안내
        send_sms([{"recipientNo": order.artist.phone.national_number}], """
            [작업터]\n- 작품명: {art_name}\n환불이 진행될 예정입니다.
        """.format(art_name=art_name))
        # 관리자 안내
        send_sms([{"recipientNo": "01027251365"}], """
            [환불 접수]\n{order_id}, {art_name}\n환불 요청 확인하세요~
        """.format(order_id=order_id, art_name=art_name))

        return RequestRefund(success=True)


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

        if order.status >= Order.REFUND:
            return UpdateOrder(success=False, msg="주문 상태를 변경할 수 없는 단계입니다.")

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

        order.status = status
        order.save()

        art_name = order.art_name[:8] + \
            '..' if len(order.art_name) > 8 else order.art_name
        message = ''

        if status == Order.PREPARE_DELIVERY:
            message = \
                "[작업터] 배송 준비 중\n" + \
                "- 주문번호: " + order_id + "\n" + \
                "- 작품명: " + art_name + "\n" + \
                "작가가 주문을 확인하여\n" + \
                "정성스레 배송 준비 중에 있습니다.\n" + \
                "작품 배송은 일반 상품 배송보다 기간이 더 소요되는 편입니다.\n" + \
                "양해 부탁드립니다. 감사합니다 :)"

        if status == Order.ON_DELIVERY:
            message = \
                "[작업터] 배송 시작 안내\n" + \
                "- 주문번호: " + order_id + "\n" + \
                "- 작품명: " + art_name + "\n" + \
                "작품 배송이 시작됐습니다.\n\n" + \
                "- 배송회사: " + delivery_company + "\n" + \
                "- 송장번호: " + delivery_number + "\n\n" + \
                "조금만 더 기다리시면 구매하신 작품을 만나보실 수 있습니다.\n" + \
                "작업터를 이용해주셔서 감사합니다 :)"

        if status == Order.DELIVERY_COMPLETED:
            message = \
                "[작업터] 배송 완료\n" + \
                "- 주문번호: " + order_id + "\n" + \
                "- 작품명: " + art_name + "\n" + \
                "작품 배송이 완료됐습니다.\n" + \
                "작품은 마음에 드셨는지요? ^-^\n" + \
                "작품을 확인하셨다면 7일 이내에 '구매확정' 또는 '환불요청' 부탁드립니다.\n" + \
                "7일 이후엔 자동으로 '구매확정' 됨을 안내드립니다.\n" + \
                "작업터를 이용해주셔서 감사합니다 :)"

        # 고객 안내
        send_lms([{"recipientNo": order.userinfo.phone.national_number}], message)

        return UpdateOrder(success=True)


class CheckUserEmail(Mutation):
    class Arguments:
        email = String(required=True)

    result = Boolean()

    def mutate(self, info, email):
        try:
            User.objects.get(username=email)
            return CheckUserEmail(result=True)
        except User.DoesNotExist:
            return CheckUserEmail(result=False)


class Mutation(ObjectType):
    create_user = CreateUser.Field()
    create_artist = CreateArtist.Field()
    like_artist = LikeArtist.Field()
    cancel_like_artist = CancelLikeArtist.Field()
    create_order = CreateOrder.Field()
    cancel_order = CancelOrder.Field()
    update_order = UpdateOrder.Field()
    complete_order = CompleteOrder.Field()
    check_user_email = CheckUserEmail.Field()
    request_refund = RequestRefund.Field()
