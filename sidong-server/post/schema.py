from graphene import Field, Int, String, List, Mutation, Boolean, ObjectType
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from post.models import Post
from file.models import upload_file


class PostType(DjangoObjectType):
    class Meta:
        model = Post


class CreatePost(Mutation):
    class Arguments:
        title = String(required=True)
        thumbnail = Upload(required=True)

    success = Boolean()

    def mutate(self, info, title, thumbnail):
        print("thumbnail:", thumbnail)
        print("title:", title)
        # Post.objects.create(title=title, thumbnail=thumbnail[0])
        upload_file(thumbnail[0])
        return CreatePost(success=True)


class Mutation(ObjectType):
    create_post = CreatePost.Field()


class Query(object):
    post = Field(PostType, id=Int(), title=String())
    # all_posts = List(PostType)

    def resolve_post(self, info, **kwargs):
        id = kwargs.get("id")
        title = kwargs.get("title")

        if id is not None:
            return Post.objects.get(id=id)

        if title is not None:
            return Post.objects.get(title=title)

        return None
