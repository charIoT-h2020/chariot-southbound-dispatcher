# -*- coding: utf-8 -*-
from consumer import Client


class MessageGenerator(Client):
    pass


# Initialize connection to southbound
broker = '172.18.1.2'
client_id = 'chariot_log_storage_demo'

producer = MessageGenerator(client_id, broker)
producer.publish('storage/urn:ngsi-ld:temp:001', '0')
producer.start(False)
