from django.http import HttpResponse
from django.shortcuts import redirect
from django.db import transaction
from art.models import Art
from user.func import create_order, create_payment, \
    update_or_create_userinfo, validate_payment


@transaction.atomic
def create_order_on_mobile(request):
    art_id = request.GET.get('artId')
    address = request.GET.get('address')
    name = request.GET.get('name')
    phone = request.GET.get('phone')
    recipient_address = request.GET.get('recipientAddress')
    recipient_name = request.GET.get('recipientName')
    recipient_phone = request.GET.get('recipientPhone')
    imp_success = request.GET.get('imp_success')
    imp_uid = request.GET.get('imp_uid')

    # if request.user.is_anonymous:
    #     return HttpResponse('<script>alert("로그인 부탁드립니다.")</script>')

    if imp_success is False:
        return HttpResponse('<script>alert("결제에 실패했습니다.\n{0}")</script>'.format(request.GET.get('error_msg')))

    art = Art.objects.get(id=art_id)
    if art.sale_status != Art.ON_SALE:
        return HttpResponse('<script>alert("판매 중인 작품이 아닙니다.")</script>')

    result_of_payment, msg_or_payment_info = validate_payment(
        imp_uid, art.price)

    if result_of_payment is False:
        return HttpResponse('<script>alert("{0}")</script>'.format(msg_or_payment_info))

    userinfo = update_or_create_userinfo(user, name, phone, address)

    result_of_create_order, msg_or_order = create_order(
        art, userinfo, recipient_address, recipient_name, recipient_phone)

    if result_of_create_order is False:
        return HttpResponse('<script>alert("{0}")</script>'.format(msg_or_order))

    result_of_create_payment, msg = create_payment(
        msg_or_payment_info, msg_or_order)

    if result_of_create_payment is False:
        return HttpResponse('<script>alert("{0}")</script>'.format(msg))

    msg_or_order.status = Order.SUCCESS
    msg_or_order.save()

    art.sale_status = Art.SOLD_OUT
    art.save()
    # TODO: SMS 전송
    # 주문/결제 정보 메세지
    # TO: 주문자, 작가
    return redirect("https://www.jakupteo.com/account/orders")
