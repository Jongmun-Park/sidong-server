from django.contrib import admin
from art.models import Art, Theme, Style, Technique


class ArtAdmin(admin.ModelAdmin):
    pass


class ThemeAdmin(admin.ModelAdmin):
    pass


class StyleAdmin(admin.ModelAdmin):
    pass


class TechniqueAdmin(admin.ModelAdmin):
    pass


admin.site.register(Art, ArtAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(Technique, TechniqueAdmin)
