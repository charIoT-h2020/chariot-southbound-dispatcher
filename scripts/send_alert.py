# -*- coding: utf-8 -*-
import json
from chariot_log_storage.connector.local import LocalConnector


class MessageGenerator(LocalConnector):
    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


# Initialize connection to southbound
broker = '172.18.1.3'
client_id = 'chariot_log_alert_demo'

producer = MessageGenerator(client_id, broker)
alert = {
    'severity': 100,
    'message': 'Sensor urn:ngsi-ld:temp:001 returns sensitive information'
}
producer.publish('alerts', json.dumps(alert))
producer.start(False)
