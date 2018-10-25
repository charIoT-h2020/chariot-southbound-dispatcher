# -*- coding: utf-8 -*-

import uuid
import json

from chariot_base.connector import WatsonConnector, LocalConnector
from chariot_base.datasource import LocalDataSource, DataPoint


class LogDigester(LocalConnector):
    def __init__(self, client_od, mqtt_broker):
        super(LogDigester, self).__init__(client_od, mqtt_broker)
        self.connector = None
        self.local_storage = None

    def on_message(self, client, userdata, message):
        point = self.to_data_point(message)
        self.store_to_local(point)
        point.message['timestamp'] = point.timestamp
        self.forward_to_engines(point, message.topic)
        self.store_to_global(point)

    def on_log(self, client, userdata, level, buf):
        print("log: ", buf)

    def set_up_watson(self):
        self.connector = WatsonConnector()

    def set_up_local_storage(self):
        self.local_storage = LocalDataSource()

    def forward_to_engines(self, point, topic):
        sensor_type, sensor_id = self.get_sensor_info(topic)
        if sensor_type == 0:
            for attr in point.message:
                message_meta = {
                    'value': point.message[attr],
                    'sensor_id': '%s_%s' % (sensor_id, attr)
                }
                self.publish('privacy', json.dumps(message_meta))
        else:
            message_meta = {
                'value': point.message,
                'sensor_id': sensor_id
            }
            self.publish('privacy', json.dumps(message_meta))

    def store_to_local(self, point):
        if self.local_storage is not None:
            self.local_storage.publish(point)

    def store_to_global(self, point):
        if self.connector is not None:
            self.connector.publish(point)

    def disconnect(self, point):
        if self is not None:
            self.connector.publish(point)

    @staticmethod
    def to_data_point(message):
        point = DataPoint('fog_logs', 'message', message, 'd')
        print("(%s) message received(%s): %s" % (message.topic, message.retain, point.message))
        return point

    @staticmethod
    def get_sensor_info(topic):
        topic = topic.replace('dispatcher/', '')

        gateways_ids = {
            'iot-2/evt/nms_status/fmt/json': '5410ec4d1601'
        }

        if topic in gateways_ids:
            return 0, gateways_ids[topic]
        else:
            return 1, topic


def main(args=None):
    # Initialize connection to southbound
    broker = '172.18.1.2'
    client_id = '%s_chariot_southbound_dispatcher' % uuid.uuid4()

    logger = LogDigester(client_id, broker)

    logger.subscribe([
        ('dispatcher/#', 0),
        ('iot-2/evt/nms_status/fmt/json', 1)
    ])

    logger.start()


if __name__ == '__main__':
    main()
