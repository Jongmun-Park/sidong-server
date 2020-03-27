import graphene

from graphene_django.types import DjangoObjectType

from art.models import Category, Art


class CategoryType(DjangoObjectType):
    class Meta:
      model = Category


class ArtType(DjangoObjectType):
    class Meta:
        model = Art

class Query(object):
    category = graphene.Field(CategoryType,
                            id=graphene.Int(),
                            name=graphene.String())
    all_categories = graphene.List(CategoryType)
    art = graphene.Field(ArtType,
                        id=graphene.Int(),
                        name=graphene.String())
    all_arts = graphene.List(ArtType)

    def resolve_category(self, info, **kwargs):
        id = kwargs.get('id')
        name = kwargs.get('name')

        if id is not None:
            return Category.objects.get(id=id)

        if name is not None:
            return Category.objects.get(name=name)

        return None

    def resolve_all_categories(self, info, **kwargs):
        return Category.objects.all()

    def resolve_art(self, info, **kwargs):
        id = kwargs.get('id')
        name = kwargs.get('name')

        if id is not None:
            return Art.objects.get(id=id)

        if name is not None:
            return Art.objects.get(name=name)

        return None

    def resolve_all_arts(self, info, **kwargs):
        return Art.objects.select_related('category').all()
