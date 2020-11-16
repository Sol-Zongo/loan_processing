# -*- coding: utf-8 -*-
import vk
import time
from settings import token

session = vk.Session()
api = vk.API(session, v=5.21)


def send_message(user_id, message, attachment=""):
    time.sleep(0.3)
    api.messages.send(
        access_token=token,
        user_id=str(user_id),
        message=message,
        attachment=attachment
    )
