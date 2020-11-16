# -*- coding: utf-8 -*-
import json
import urllib
import urllib.request
from settings import billing_ip
from settings import sms_api_key


class Api(object):
    def __init__(self, srv_address=billing_ip):
        self.srv_address = srv_address

    def call_api(self, model, params):
        encoded_params = urllib.parse.urlencode(params).encode("utf-8")
        api_url = "{0}/rest_api/v2/{1}/".format(self.srv_address, model)

        req = urllib.request.Request(api_url, encoded_params)
        response = urllib.request.urlopen(req)
        result = response.read()
        obj = json.loads(result)
        return obj


class SmsApi(object):
    def __init__(self, srv_address='https://sms.ru', api_id=sms_api_key):
        self.srv_address = srv_address
        self.api_id = api_id

    def call_api(self, params):
        encoded_params = urllib.parse.urlencode(params).encode("utf-8")
        api_url = "{0}/sms/send?".format(self.srv_address)
        req = urllib.request.Request(api_url, encoded_params)
        response = urllib.request.urlopen(req)
        result = response.read()
        # obj = json.loads(result)  # Иногда нужно декодировать obj = json.loads(result.decode())
        obj = json.loads(result.decode())
        # if obj.get('error'):
        #     print(u'Произошла ошибка на стороне sms.ru:{0}'.format(obj['error']))
        return obj

    def send_sms(self, phone, message):
        params = {
            'api_id': self.api_id,
            'to': str(phone),
            'msg': str(message),
            'json': 1
        }
        res_dict = self.call_api(params=params)
        return res_dict


def get_abonent_id(bill):
    params = {
        'method1': 'objects.filter',
        'arg1': '{"login":"' + bill + '"}'
    }
    client = Api()
    # Документация Users - http://demo5.carbonsoft.ru/rest_api/v2/Users/
    res_dict = client.call_api(model='Users', params=params)
    m_list = []
    if res_dict['result'] == m_list:
        return None
    try:
        for row in res_dict['result']:
            if res_dict['result'] == m_list:
                return None
            else:
                ab_id = str(row['fields']['abonent_id'])
                return ab_id
    except Exception as e:
        return 'Невозможно получить ID абонента\n\n' + str(e) + '\n'


def filter_subscribers_by_tariff(tariff_list):
    users_list = []
    for tariff in tariff_list:
        params = {
            'method1': 'objects.filter',
            'arg1': '{"tarif_id":"' + str(tariff) + '"}',
        }
        client = Api()
        # Users Документация - http://demo5.carbonsoft.ru/rest_api/v2/Abonents/
        res_dict = client.call_api(model='Abonents', params=params)

        if 'result' in res_dict:
            if res_dict['result']:
                for user in res_dict['result']:
                    user_data = {
                        'bill': user['fields']['contract_number'],
                        'tariff': str(tariff),
                        # 'activate_date': user['fields']['activate_date']
                    }
                    users_list.append(user_data)

    return users_list


def user_paylog(bill, usluga_id_list):
    payments_sum = 0.0
    user_id = get_abonent_id(bill)
    if str(user_id).isdigit():
        params = {
            'method1': 'objects.filter',
            'arg1': '{"abonent_id": "' + str(user_id) + '"}',
        }
        client = Api()
        #  Документация UsersCache - http://demo5.carbonsoft.ru/rest_api/v2/FinanceOperations/
        res_dict = client.call_api(model='Counters', params=params)
        if res_dict:
            if 'result' in res_dict:
                for payment in res_dict['result']:
                    if str(payment['fields']['usluga_id']) in usluga_id_list:
                        if str(payment['fields']['summ']).replace('.', '', 1).isdigit():
                            payments_sum += float(payment['fields']['summ']).__round__()
                return payments_sum


def tariff_change(bill, tariff_id):
    user_id = get_abonent_id(bill)
    if str(user_id).isdigit():
        params = {
            'method1': 'objects.get',
            'arg1': '{"id": "' + str(user_id) + '"}',
            'method2': 'set',
            'arg2': '{"tarif_id": "' + str(tariff_id) + '"}',
            'method3': 'save',
            'arg3': '{}',
        }
        client = Api()
        #  Документация UsersCache - http://demo5.carbonsoft.ru/rest_api/v2/FinanceOperations/
        res_dict = client.call_api(model='Abonents', params=params)
        if res_dict:
            if 'result' in res_dict:
                return None


def get_abonent_phone(bill):
    user_id = get_abonent_id(bill)
    if user_id:
        if str(user_id).isdigit():
            params = {
                'method1': 'objects.filter',
                'arg1': '{"id":"' + user_id + '"}'
            }
            client = Api()
            #  UsersCache Документация - http://demo5.carbonsoft.ru/rest_api/v2/UsersCache/
            res_dict = client.call_api(model='Abonents', params=params)
            if res_dict['result']:
                sms = res_dict['result'][0]['fields']['sms']
                if sms == '':
                    return None
                return sms
