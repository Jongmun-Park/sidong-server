from graphene import ObjectType, Field, List, ID
from graphene_django.types import DjangoObjectType
from art.models import Theme, Style, Technique


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

    def resolve_art_options(parent, info, medium_id):
        themes = Theme.objects.filter(medium=medium_id)
        styles = Style.objects.filter(medium=medium_id)
        techniques = Technique.objects.filter(medium=medium_id)
        return ArtOptions(
            themes=themes,
            styles=styles,
            techniques=techniques,
        )
