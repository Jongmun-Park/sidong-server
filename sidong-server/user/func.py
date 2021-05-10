import requests
import datetime
import pytz
from django.conf import settings
from user.models import Payment


def get_access_token_of_imp():
    try:
        response = requests.post('https://api.iamport.kr/users/getToken', json={
            'imp_key': settings.IMP_ACCESS_KEY,
            'imp_secret': settings.IMP_SECRET_ACCESS_KEY,
        })
        return response.json()['response']['access_token']
    except:
        return None


def validate_payment(imp_uid, art_price):
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

    if payment_info.get('amount') != art_price:
        # TODO: 결제 취소
        return (False, '결제 금액에 문제가 있습니다.\n결제된 금액: ' + payment_info.get('amount'))

    return (True, payment_info)


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
