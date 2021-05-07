import requests
from django.conf import settings


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
    except:
        return (False, '결제 정보 확인 중 문제가 발생했습니다.')

    if not payment_info:
        return (False, '결제 정보가 없습니다.')

    if payment_info.get('status') != 'paid':
        return (False, '결제가 완료되지 않았습니다. 상태: {0}'.format(payment_info.get('status')))

    if payment_info.get('amount') != art_price:
        # TODO: 결제 취소
        return (False, '결제 금액에 문제가 있습니다. 결제된 금액: {0}'.format(payment_info.get('amount')))

    return (True, payment_info)
