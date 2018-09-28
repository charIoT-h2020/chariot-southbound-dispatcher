# -*- coding: utf-8 -*-
import json
from chariot_base.connector import LocalConnector


class MessageGenerator(LocalConnector):
    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


# Initialize connection to southbound
broker = '172.18.1.2'
client_id = 'chariot_log_storage_demo'

producer = MessageGenerator(client_id, broker)
log = {
    'd': {
        'temperature': -10.1,
        'humidity': 40.1
    }
}
producer.publish('dispatcher/urn:ngsi-ld:temp:001', json.dumps(log))
producer.start(False)
