# -*- coding: utf-8 -*-
from connector import LocalConnector
from datasource import LocalDataSource, DataPoint


local_storage = LocalDataSource()


class MessageLogger(LocalConnector):

    @staticmethod
    def on_message(client, userdata, message):
        point = DataPoint('fog_logs', 'alerts', message)
        local_storage.publish(point)

        if message.retain == 1:
            print("This is a retained message")

    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


if __name__ == '__main__':
    # Initialize connection to northbound
    broker = '172.18.1.3'
    client_id = 'chariot_log_alert'

    logger = MessageLogger(client_id, broker)

    logger.subscribe([
        ('alerts/#', 0)
    ])

    logger.start()
