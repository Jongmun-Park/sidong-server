from django.db import transaction
from graphene import ObjectType, Field, List, ID, Mutation, String, \
    Int, Boolean, Argument, InputObjectType, InputField
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from art.models import Theme, Style, Technique, Art, \
    calculate_art_size, Like
from file.models import File, create_file, validate_file


class ArtImageType(ObjectType):
    id = ID()
    url = String()


class ArtType(DjangoObjectType):
    class Meta:
        model = Art
        convert_choices_to_enum = ["size"]

    representative_image_url = String()
    image_urls = List(ArtImageType)
    current_user_likes_this = Boolean()

    def resolve_representative_image_url(self, info):
        return self.representative_image_url

    def resolve_image_urls(self, info):
        image_urls = []
        for image_id in self.images:
            file_instance = File.objects.get(id=image_id)
            image_urls.append({
                'id': image_id,
                'url': file_instance.url,
            })

        return image_urls

    def resolve_current_user_likes_this(self, info):
        user = info.context.user
        if user.is_anonymous:
            return False
        return Like.objects.filter(user=user, art_id=self.id).exists()


class ThemeType(DjangoObjectType):
    class Meta:
        model = Theme
        convert_choices_to_enum = False


class StyleType(DjangoObjectType):
    class Meta:
        model = Style
        convert_choices_to_enum = False


class TechniqueType(DjangoObjectType):
    class Meta:
        model = Technique
        convert_choices_to_enum = False


class ArtOptions(ObjectType):
    themes = List(ThemeType)
    styles = List(StyleType)
    techniques = List(TechniqueType)


class ArtLikeType(DjangoObjectType):
    class Meta:
        model = Like


class SaleStatusInput(InputObjectType):
    on_sale = InputField(Boolean)
    sold_out = InputField(Boolean)
    not_for_sale = InputField(Boolean)


class OrientationInput(InputObjectType):
    landscape = InputField(Boolean)
    portrait = InputField(Boolean)
    square = InputField(Boolean)
    etc = InputField(Boolean)


class ArtSizeInput(InputObjectType):
    small = InputField(Boolean)
    medium = InputField(Boolean)
    large = InputField(Boolean)


class Query(ObjectType):
    art = Field(ArtType, art_id=ID())
    art_options = Field(ArtOptions, medium_id=ID())
    arts = List(ArtType, last_art_id=ID(),
                page_size=Int(), sale_status=Argument(SaleStatusInput),
                orientation=Argument(OrientationInput), size=Argument(ArtSizeInput),
                price=List(Int), medium=String(), style=String(),
                technique=String(), theme=String())
    arts_by_artist = List(ArtType, artist_id=ID(), last_art_id=ID())

    def resolve_art(self, info, art_id):
        return Art.objects.get(id=art_id)

    def resolve_art_options(parent, info, medium_id):
        themes = Theme.objects.filter(medium=medium_id)
        styles = Style.objects.filter(medium=medium_id)
        techniques = Technique.objects.filter(medium=medium_id)
        return ArtOptions(
            themes=themes,
            styles=styles,
            techniques=techniques,
        )

    def resolve_arts(self, info, last_art_id=None, page_size=20,
                     sale_status=None, size=None, orientation=None, price=None,
                     medium=None, theme=None, style=None, technique=None):

        arts_filter = {}
        id_filter = {}

        if sale_status:     # 필터 적용
            sale_status_list = []
            orientation_list = []
            size_list = []

            if sale_status['on_sale'] is True:
                sale_status_list.append(Art.ON_SALE)
            if sale_status['sold_out'] is True:
                sale_status_list.append(Art.SOLD_OUT)
            if sale_status['not_for_sale'] is True:
                sale_status_list.append(Art.NOT_FOR_SALE)

            if orientation['landscape'] is True:
                orientation_list.append(Art.LANDSCAPE)
            if orientation['portrait'] is True:
                orientation_list.append(Art.PORTRAIT)
            if orientation['square'] is True:
                orientation_list.append(Art.SQUARE)
            if orientation['etc'] is True:
                orientation_list.append(Art.ETC_ORIENTATION)

            if size['small'] is True:
                size_list.append(Art.SMALL)
            if size['medium'] is True:
                size_list.append(Art.MEDIUM)
            if size['large'] is True:
                size_list.append(Art.LARGE)

            if medium != 'all':
                arts_filter['medium'] = medium
            if style != 'all':
                arts_filter['style'] = style
            if technique != 'all':
                arts_filter['technique'] = technique
            if theme != 'all':
                arts_filter['theme'] = theme

            arts_filter['sale_status__in'] = sale_status_list
            arts_filter['orientation__in'] = orientation_list
            arts_filter['size__in'] = size_list
            arts_filter['price__range'] = price

        if arts_filter:
            arts = Art.objects.filter(**arts_filter)
        else:
            arts = Art.objects.all()

        if not arts:
            return None

        if last_art_id is None:
            id_filter['id__lte'] = arts.last().id
        else:
            id_filter['id__lt'] = last_art_id

        return arts.filter(**id_filter).order_by('-id')[:page_size]

    def resolve_arts_by_artist(self, info, artist_id, last_art_id=None):
        arts_filter = {'id__lt': last_art_id}
        arts = Art.objects.filter(artist_id=artist_id)

        if not arts:
            return None

        if last_art_id is None:
            last_art_id = arts.last().id
            arts_filter = {'id__lte': last_art_id}

        return arts.filter(**arts_filter).order_by('-id')[:12]


class CreateArt(Mutation):
    class Arguments:
        art_images = Upload(required=True)
        description = String(required=True)
        width = Int(required=True)
        height = Int(required=True)
        is_framed = Boolean(required=True)
        medium = ID(required=True)
        name = String(required=True)
        orientation = ID(required=True)
        price = Int()
        sale_status = ID(required=True)
        style = ID(required=True)
        technique = ID(required=True)
        theme = ID(required=True)

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, art_images, description, width,
               height, is_framed, medium, name, orientation,
               sale_status, style, technique, theme, price=None):
        current_user = info.context.user

        for image in art_images:
            validate_image = validate_file(image, File.BUCKET_ASSETS)
            if validate_image['status'] == 'fail':
                return CreateArt(success=False, msg=validate_image['msg'])

        image_file_ids = []

        for image in art_images:
            image_file = create_file(image, File.BUCKET_ASSETS, current_user)
            if image_file['status'] == 'fail':
                return CreateArt(success=False, msg=image_file['msg'])
            image_file_ids.append(image_file['instance'].id)

        Art.objects.create(
            artist=current_user.artist,
            images=image_file_ids,
            description=description,
            width=width,
            height=height,
            size=calculate_art_size(width, height),
            is_framed=is_framed,
            medium=medium,
            name=name,
            orientation=orientation,
            price=price,
            sale_status=sale_status,
            style=Style.objects.get(id=style),
            technique=Technique.objects.get(id=technique),
            theme=Theme.objects.get(id=theme),
        )

        return CreateArt(success=True)


class LikeArt(Mutation):
    class Arguments:
        art_id = ID(required=True)

    success = Boolean()

    def mutate(self, info, art_id):
        user = info.context.user
        if user.is_anonymous:
            return LikeArt(success=False)

        art = Art.objects.get(id=art_id)
        try:
            Like.objects.create(user=user, art=art)
        except:
            # unique constraint 에러 처리를 위한 GraphQLLocatedError가 import 되지 않아
            # 임시적으로 모든 에러를 예외 처리
            return LikeArt(success=True)

        return LikeArt(success=True)


class CancelLikeArt(Mutation):
    class Arguments:
        art_id = ID(required=True)

    success = Boolean()

    def mutate(self, info, art_id):
        user = info.context.user
        if user.is_anonymous:
            return CancelLikeArt(success=False)

        like = Like.objects.filter(user=user, art_id=art_id)
        like.delete()
        return CancelLikeArt(success=True)


class Mutation(ObjectType):
    create_art = CreateArt.Field()
    like_art = LikeArt.Field()
    cancel_like_art = CancelLikeArt.Field()
