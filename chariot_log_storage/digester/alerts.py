# -*- coding: utf-8 -*-
import uuid
from chariot_log_storage.chariot_log_storage.connector import LocalConnector
from chariot_log_storage.chariot_log_storage.datasource import LocalDataSource, DataPoint


local_storage = LocalDataSource()


class AlertDigester(LocalConnector):

    @staticmethod
    def on_message(client, userdata, message):
        point = DataPoint('fog_logs', 'alerts', message)
        local_storage.publish(point)

        if message.retain == 1:
            print("This is a retained message")

    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


def main(args = None):
    # Initialize connection to northbound
    broker = '172.18.1.3'
    client_id = '%s_chariot_log_alert' % uuid.uuid4()

    logger = AlertDigester(client_id, broker)

    logger.subscribe([
        ('alerts/#', 0)
    ])

    logger.start()


if __name__ == '__main__':
    main()
