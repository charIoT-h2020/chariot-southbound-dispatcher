# -*- coding: utf-8 -*-
import uuid
from ..connector import WatsonConnector, LocalConnector
from ..datasource import LocalDataSource, DataPoint

connector = WatsonConnector()
local_storage = LocalDataSource()


class LogDigester(LocalConnector):
    def __init__(self, client_od, mqtt_broker):
        super(LogDigester, self).__init__(client_od, mqtt_broker)

    @staticmethod
    def on_message(client, userdata, message):
        point = DataPoint('fog_logs', 'message', message, 'd')

        print("(%s) message received(%s): %s" % (message.topic, message.retain, point.message))

        local_storage.publish(point)
        connector.publish(point)

        if message.retain == 1:
            print("This is a retained message")

    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


def main(args=None):
    # Initialize connection to southbound
    broker = '172.18.1.2'
    client_id = '%s_chariot_log_storage' % uuid.uuid4()

    logger = LogDigester(client_id, broker)

    logger.subscribe([
        ('dispatcher/#', 0),
        ('iot-2/evt/nms_status/fmt/json', 1)
    ])

    logger.start()


if __name__ == '__main__':
    main()
