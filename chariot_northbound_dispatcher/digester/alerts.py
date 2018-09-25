# -*- coding: utf-8 -*-
import uuid
from ..connector import LocalConnector
from ..datasource import LocalDataSource, DataPoint


class AlertDigester(LocalConnector):
    def __init__(self, client_od, broker):
        super(AlertDigester, self).__init__(client_od, broker)
        self.local_storage = LocalDataSource()

    def on_message(self, client, userdata, message):
        point = DataPoint('fog_logs', 'alerts', message)
        self.local_storage.publish(point)

        if message.retain == 1:
            print("This is a retained message")

    def on_log(self, client, userdata, level, buf):
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
