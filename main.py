# -*- coding: utf-8 -*-
import billing_api
import math
import vkapi
from settings import admins_list, tariffs, default_tariff, default_tariff_name


def chunks(string, n):
    """
    Разделяет строки на заданные отрезки
    :param string: Str
    :param n: Int
    :return: List
    """
    for start in range(0, len(string), n):
        yield string[start:start + n]


def find_users(all_tariffs):
    """
    Поиск всех абонентов с указанными тарифами
    :param all_tariffs: dict
    :return: list
    """
    tariff_list = []

    for i, j in all_tariffs.items():
        tariff_list.append(j['tariff_id'])

    return billing_api.filter_subscribers_by_tariff(tariff_list)


def calculate_payments(users_list, all_tariffs):
    """
    Суммируем у каждого абонента платежи по выбранной услуге
    :param users_list: list
    :param all_tariffs: dict
    :return: list
    """
    usluga_id_list = []
    users_payments = []

    for key, value in all_tariffs.items():
        usluga_id_list.append(value['usluga_id'])

    for user in users_list:
        user['payments'] = billing_api.user_paylog(user['bill'], usluga_id_list)
        for key, value in all_tariffs.items():
            if value['tariff_id'] == user['tariff']:
                user['t_all_sum'] = value['t_all_sum']
                user['tariff_name'] = key
                user['payments_left'] = math.ceil(
                    (int(value['t_all_sum']) - int(user['payments'])) / int(value['payment_sum'])
                )
        users_payments.append(user)

    return users_payments


def send_reports(admins_report_list, report_message):
    """
    Отправка отчета в ВК через сообщество
    :param admins_report_list: list
    :param report_message: str
    :return: None
    """
    if len(admins_report_list) > 0:
        for user_id in admins_report_list:
            # Если количество символов в сообщении превысит допустимое
            if len(report_message) > 1000:
                for chunk in chunks(report_message, 1000):
                    vkapi.send_message(user_id, chunk)
            else:
                vkapi.send_message(user_id, report_message)


def main():
    users = find_users(tariffs)  # Ищем всех абонентов с указанными тарифами

    sum_users_payments = calculate_payments(users, tariffs)  # Суммируем у каждого платежи по выбранной услуге

    report = f'&#128197; Отчет по абонентам с рассрочкой &#128197;' \
             f'\n\n Всего абонентов с рассрочкой: {str(len(users))}\n\n'

    for user_payment in sum_users_payments:
        if int(user_payment['payments']) >= int(user_payment['t_all_sum']):

            # Меняем тариф
            billing_api.tariff_change(user_payment['bill'], default_tariff)

            # Оповещаем абонента о погашении рассрочки
            message = f'Рассрочка по договору {user_payment["bill"]} погашена'
            user_phone = billing_api.get_abonent_phone(user_payment['bill'])
            if user_phone:
                sms_sender = billing_api.SmsApi()
                sms_sender.send_sms(user_phone, message)

            report = report + f'&#9989; {user_payment["bill"]} Рассрочка оплачена, абонент переведен на тариф ' \
                              f'{default_tariff_name}\n'
        else:
            message = f'{user_payment["bill"]}\n' + \
                      f'Тариф: {user_payment["tariff_name"]}\n' + \
                      f'Оплачено по тарифу: {user_payment["payments"]} руб.\n' + \
                      f'Осталось платежей: {user_payment["payments_left"]}\n\n'
            report = report + message

    send_reports(admins_list, report)
