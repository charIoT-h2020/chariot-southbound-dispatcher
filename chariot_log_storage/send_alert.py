# -*- coding: utf-8 -*-
from consumer import Client


class MessageGenerator(Client):
    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


# Initialize connection to southbound
broker = '172.18.1.3'
client_id = 'chariot_log_alert_demo'

producer = MessageGenerator(client_id, broker)
producer.publish('alerts', 'Sensor urn:ngsi-ld:temp:001 returns sensitive information,100')
producer.start(False)
