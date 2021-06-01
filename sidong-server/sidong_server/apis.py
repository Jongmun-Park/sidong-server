from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.db import transaction
from art.models import Art
from user.models import Order
from user.func import create_order, create_payment, \
    update_or_create_userinfo, validate_payment, send_sms


@transaction.atomic
def create_order_on_mobile(request):
    art_id = request.GET.get('artId')
    user_id = request.GET.get('userId')
    address = request.GET.get('address')
    name = request.GET.get('name')
    phone = request.GET.get('phone')
    recipient_address = request.GET.get('recipientAddress')
    recipient_name = request.GET.get('recipientName')
    recipient_phone = request.GET.get('recipientPhone')
    imp_success = request.GET.get('imp_success')
    imp_uid = request.GET.get('imp_uid')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponse('<script>alert("로그인 정보가 없습니다.")</script>')

    if imp_success != "true":
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

    art_name = art.name[:8] + \
        '..' if len(art.name) > 8 else art.name

    # 고객 안내
    send_sms([{"recipientNo": phone}], """
            [작업터]\n- 작품명: {art_name}\n주문 완료.\n감사합니다.
        """.format(art_name=art_name))
    # 작가 안내
    send_sms([{"recipientNo": art.artist.phone.national_number}], """
            [작업터]\n- 작품명: {art_name}\n주문이 접수됐습니다.\n확인 바랍니다.
        """.format(art_name=art_name))

    return redirect("https://www.jakupteo.com/account/orders")
