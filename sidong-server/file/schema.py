from graphene_django.types import DjangoObjectType
from graphene import Field, ID, String, ObjectType
from file.models import File


class FileType(DjangoObjectType):
    class Meta:
        model = File

    url = String()

    def resolve_url(self, info):
        return self.url


class Query(ObjectType):
    file = Field(FileType, file_id=ID())

    def resolve_file(self, info, file_id):
        return File.objects.get(id=file_id)
