from django.db import transaction

from graphene import ObjectType, Field, List, ID, Mutation, String, Int, Boolean
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from art.models import Theme, Style, Technique, Art, calculate_art_size
from file.models import File, create_file, validate_file


class ArtType(DjangoObjectType):
    class Meta:
        model = Art


class ThemeType(DjangoObjectType):
    class Meta:
        model = Theme


class StyleType(DjangoObjectType):
    class Meta:
        model = Style


class TechniqueType(DjangoObjectType):
    class Meta:
        model = Technique


class ArtOptions(ObjectType):
    themes = List(ThemeType)
    styles = List(StyleType)
    techniques = List(TechniqueType)


class Query(ObjectType):
    art_options = Field(ArtOptions, medium_id=ID())
    arts = List(ArtType, last_art_id=ID(), page_size=Int())

    def resolve_art_options(parent, info, medium_id):
        themes = Theme.objects.filter(medium=medium_id)
        styles = Style.objects.filter(medium=medium_id)
        techniques = Technique.objects.filter(medium=medium_id)
        return ArtOptions(
            themes=themes,
            styles=styles,
            techniques=techniques,
        )

    def resolve_arts(self, info, last_art_id=None, page_size=12):
        arts_filter = {'id__lt': last_art_id}

        if last_art_id is None:
            last_art_id = Art.objects.last().id
            arts_filter = {'id__lte': last_art_id}

        return Art.objects.filter(
            **arts_filter,
        ).order_by('-id')[:page_size]


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
        price = Int(required=True)
        sale_status = ID(required=True)
        style = ID(required=True)
        technique = ID(required=True)
        theme = ID(required=True)

    success = Boolean()
    msg = String()

    @transaction.atomic
    def mutate(self, info, art_images, description, width,
               height, is_framed, medium, name, orientation,
               price, sale_status, style, technique, theme):
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


class Mutation(ObjectType):
    create_art = CreateArt.Field()
