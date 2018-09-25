# -*- coding: utf-8 -*-
from chariot_log_storage.chariot_log_storage.connector.local import LocalConnector


class MessageGenerator(LocalConnector):
    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


# Initialize connection to southbound
broker = '172.18.1.3'
client_id = 'chariot_log_alert_demo'

producer = MessageGenerator(client_id, broker)
producer.publish('alerts', 'Sensor urn:ngsi-ld:temp:001 returns sensitive information,100')
producer.start(False)
