from django.urls import path
from django.contrib import admin
from graphene_file_upload.django import FileUploadGraphQLView
from sidong_server import apis

urlpatterns = [
    path("admin", admin.site.urls),
    path("graphql", FileUploadGraphQLView.as_view(graphiql=True)),
    path("api/create/order", apis.create_order_on_mobile),
]
