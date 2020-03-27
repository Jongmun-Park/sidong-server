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
    all_categories = graphene.List(CategoryType)
    all_arts = graphene.List(Art)

    def resolve_all_categories(self, info, **kwargs):
        return Category.objects.all()

    def resolve_all_arts(self, info, **kwargs):
        return Art.objects.select_related('category').all()
