import requests
import datetime
import pytz
from django.conf import settings
from user.models import Payment, UserInfo, Order


def send_sms(recipient_list, content):
    try:
        requests.post(
            'https://api-sms.cloud.toast.com/sms/v2.4/appKeys/' +
            settings.TOAST_APP_KEY+'/sender/sms',
            json={
                "body": content,
                "sendNo": "01027251365",
                "recipientList": recipient_list,
            }
        )
    except:
        # TODO: 문자 전송 실패 에러 처리
        pass


def send_lms(recipient_list, content):
    try:
        requests.post(
            'https://api-sms.cloud.toast.com/sms/v2.4/appKeys/' +
            settings.TOAST_APP_KEY+'/sender/mms',
            json={
                "title": "작업터 안내 문자",
                "body": content,
                "sendNo": "01027251365",
                "recipientList": recipient_list,
            }
        )
    except:
        # TODO: 문자 전송 실패 에러 처리
        pass


def get_access_token_of_imp():
    try:
        response = requests.post('https://api.iamport.kr/users/getToken', json={
            'imp_key': settings.IMP_ACCESS_KEY,
            'imp_secret': settings.IMP_SECRET_ACCESS_KEY,
        })
        return response.json()['response']['access_token']
    except:
        return None


def update_or_create_userinfo(user, name, phone, address):
    userinfo, _ = UserInfo.objects.update_or_create(
        user=user,
        defaults={
            'name': name,
            'phone': phone,
            'address': address,
        },
    )
    return userinfo


def create_order(art, userinfo, recipient_address, recipient_name, recipient_phone):
    try:
        order = Order.objects.create(
            userinfo=userinfo,
            art_name=art.name,
            price=art.price+art.delivery_fee,
            art=art,
            artist=art.artist,
            recipient_address=recipient_address,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            status=Order.WAIT,
        )
        return (True, order)
    except Exception as error:
        return (False, '주문(Order) 생성 중에 문제가 발생했습니다.\n' + error)


def validate_payment(imp_uid, price):
    try:
        response = requests.get('https://api.iamport.kr/payments/'+imp_uid, headers={
            'Authorization': get_access_token_of_imp(),
        })
        payment_info = response.json()['response']
    except Exception as error:
        return (False, '결제 정보 확인 중 문제가 발생했습니다.\n' + error)

    if not payment_info:
        return (False, '결제 정보가 없습니다.')

    if payment_info.get('status') != 'paid':
        return (False, '결제가 완료되지 않았습니다.\n상태: ' + payment_info.get('status'))

    if payment_info.get('amount') != price:
        # TODO: 결제 취소
        # 관리자 안내
        send_sms([{"recipientNo": "01027251365"}], """
            [결제 금액 불일치]\nimp_uid: {imp_uid}
        """.format(imp_uid=imp_uid))

        return (False, '결제 금액에 문제가 있습니다.\n결제된 금액: ' + str(payment_info.get('amount')))

    return (True, payment_info)


def create_payment(payment_info, order):
    try:
        Payment.objects.create(
            transacted_at=datetime.datetime.fromtimestamp(
                payment_info['paid_at'], pytz.timezone('Asia/Seoul')),
            transaction_id=payment_info['imp_uid'],
            order=order,
            status=payment_info['status'],
            amount=payment_info['amount'],
            pay_method=payment_info['pay_method'],
        )
        return (True, '')
    except Exception as error:
        return (False, '결제(Payment) 생성 중에 문제가 발생했습니다.\n' + error)


def cancel_payment(payment_id):
    payment = Payment.objects.get(id=payment_id)

    if payment.status != 'paid':
        return (False, '결제 완료된 주문이 아닙니다.\n주문 상태를 확인 바랍니다.')

    try:
        response = requests.post(
            'https://api.iamport.kr/payments/cancel',
            headers={
                'Authorization': get_access_token_of_imp(),
            },
            json={
                'imp_uid': payment.transaction_id,
                'checksum': payment.amount,
            }
        ).json()

        if response['code'] != 0:
            return (False, response['message'])

        cancel_result = response['response']

        Payment.objects.create(
            transacted_at=datetime.datetime.fromtimestamp(
                cancel_result['cancelled_at'], pytz.timezone('Asia/Seoul')),
            transaction_id=cancel_result['imp_uid'],
            order=payment.order,
            status=cancel_result['status'],
            amount=cancel_result['cancel_amount'],
            pay_method=cancel_result['pay_method'],
        )

        return (True, '')
    except Exception as error:
        return (False, '결제 취소 중 문제가 발생했습니다.\n' + error)
