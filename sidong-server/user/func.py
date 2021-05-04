import requests
from django.conf import settings


def get_access_token_of_imp():
    # TODO: 에러 발생시, 결제 취소
    response = requests.post('https://api.iamport.kr/users/getToken', json={
        'imp_key': settings.IMP_ACCESS_KEY,
        'imp_secret': settings.IMP_SECRET_ACCESS_KEY,
    })
    return response.json()['response']['access_token']


def validate_payment_by_imp(imp_uid, art_price):
    response = requests.get('https://api.iamport.kr/payments/'+imp_uid, headers={
        'Authorization': get_access_token_of_imp(),
    })
    payment_info = response.json()['response']

    if not payment_info:
        return '결제 정보가 없습니다.'

    if payment_info.get('status') != 'paid':
        return '결제가 완료되지 않았습니다. 상태: {0}'.format(payment_info.get('status'))

    if payment_info.get('amount') != art_price:
        # TODO: 결제 취소
        return '결제 금액에 문제가 있습니다. 결제된 금액: {0}'.format(payment_info.get('amount'))

    return True
