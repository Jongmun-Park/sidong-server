from django.urls import path, include
from django.contrib import admin

# from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView

urlpatterns = [
    path("admin/", admin.site.urls),
    # TODO: remove csrf_exempt !
    path("graphql/", GraphQLView.as_view(graphiql=True)),
    path("user/", include("user.urls")),
]
