from graphene_django.types import DjangoObjectType
from graphene import Field, ID, String
from file.models import File


class FileType(DjangoObjectType):
    class Meta:
        model = File

    url = String()

    def resolve_url(self, info):
        return self.url


class Query(object):
    file = Field(FileType, id=ID())

    def resolve_file(self, info, id):
        if id is None:
            return None
        return File.objects.get(id=id)
