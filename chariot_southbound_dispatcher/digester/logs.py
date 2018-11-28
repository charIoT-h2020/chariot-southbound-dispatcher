# -*- coding: utf-8 -*-

import uuid
import json
import gmqtt
import asyncio

from chariot_base.connector import WatsonConnector, LocalConnector
from chariot_base.model import DataPointFactory
from chariot_base.datasource import LocalDataSource


class LogDigester(LocalConnector):
    def __init__(self):
        super(LogDigester, self).__init__()
        self.connector = None
        self.point_factory = DataPointFactory('fog_logs', 'message')
        self.local_storage = None

        self.gateways_ids = {
            'iot-2/evt/nms_status/fmt/json': '5410ec4d1601'
        }

    def on_message(self, client, topic, payload, qos, properties):
        point = self.to_data_point(payload, topic)
        self.store_to_local(point)
        self.forward_to_engines(point, topic)
        self.store_to_global(point)

    def forward_to_engines(self, point, topic):
        sensor_type, sensor_id = self.get_sensor_info(topic)
        if sensor_type == 0:
            for attr in point.message:
                message_meta = {
                    'timestamp': point.timestamp,
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
            return self.local_storage.publish(point)

    def store_to_global(self, point):
        if self.connector is not None:
            return self.connector.publish(point)

    def set_up_watson(self, options):
        self.connector = WatsonConnector(options)

    def set_up_local_storage(self, options):
        self.local_storage = LocalDataSource(options['host'], options['port'], options['username'], options['password'], 'test_db')

    def to_data_point(self, message, topic):
        topic = topic.replace('dispatcher/', '')

        if topic in self.gateways_ids:
            return self.point_factory.from_json_string(message, 'd')
        else:
            return self.point_factory.from_json_string(message)

    def get_sensor_info(self, topic):
        topic = topic.replace('dispatcher/', '')

        if topic in self.gateways_ids:
            return 0, self.gateways_ids[topic]
        else:
            return 1, topic


async def main(args=None):
    # Initialize connection to southbound
    OPTS = json.load(open('tests/config.json', 'r'))

    mqtt_options = OPTS['mosquitto']
    options_watson = OPTS['iot']['client1']
    options_db = OPTS['local_storage']

    client_id = '%s_chariot_southbound_dispatcher' % uuid.uuid4()

    client = gmqtt.Client(client_id, clean_session=True)
    await client.connect(host=mqtt_options['host'], port=mqtt_options['port'], version=4)

    logger = LogDigester()
    logger.register_for_client(client)
    logger.set_up_local_storage(options_db)
    logger.set_up_watson(options_watson)

    logger.subscribe("dispatcher/#", qos=2)
    logger.subscribe('iot-2/evt/nms_status/fmt/json', qos=2)

    await asyncio.sleep(1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
