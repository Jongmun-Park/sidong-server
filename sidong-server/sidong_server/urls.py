from django.urls import path, include
from django.contrib import admin
from graphene_file_upload.django import FileUploadGraphQLView

# from graphene_django.views import GraphQLView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", FileUploadGraphQLView.as_view(graphiql=True)),
]
