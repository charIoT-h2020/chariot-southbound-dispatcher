# -*- coding: utf-8 -*-
from consumer import Client


class MessageGenerator(Client):
    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


# Initialize connection to southbound
broker = '172.18.1.2'
client_id = 'chariot_log_storage_demo'

producer = MessageGenerator(client_id, broker)
producer.publish('dispatcher/urn:ngsi-ld:temp:001', '0')
producer.start(False)
