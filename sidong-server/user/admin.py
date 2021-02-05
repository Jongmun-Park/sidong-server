from django.contrib import admin
from user.models import Artist


class ArtistAdmin(admin.ModelAdmin):
    pass


admin.site.register(Artist, ArtistAdmin)
