from django.contrib import admin
from user.models import Artist, UserInfo, Order, Payment, Refund


class ArtistAdmin(admin.ModelAdmin):
    pass


class UserInfoAdmin(admin.ModelAdmin):
    pass


class OrderAdmin(admin.ModelAdmin):
    pass


class PaymentAdmin(admin.ModelAdmin):
    pass


class RefundAdmin(admin.ModelAdmin):
    pass


admin.site.register(Artist, ArtistAdmin)
admin.site.register(UserInfo, UserInfoAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Refund, RefundAdmin)
