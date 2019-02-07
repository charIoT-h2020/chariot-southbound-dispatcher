# -*- coding: utf-8 -*-

import os  
import uuid
import json
import gmqtt
import asyncio
import signal

from chariot_base.connector import WatsonConnector, LocalConnector
from chariot_base.model import DataPointFactory
from chariot_base.datasource import LocalDataSource


class LogDigester(LocalConnector):
    def __init__(self, options):
        super(LogDigester, self).__init__()
        self.connector = None
        self.point_factory = DataPointFactory(options['database'], options['table'])
        self.local_storage = None

        self.gateways_ids = options['gateways_ids']

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
        self.local_storage = LocalDataSource(
            options['host'], options['port'], options['username'], options['password'], options['database']
        )

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


STOP = asyncio.Event()


def ask_exit(*args):
    STOP.set()


async def main(args=None):
    # Initialize connection to southbound
    filename = None
    for name in ['./config.json', './tests/config.json']:
      if os.path.isfile(name):
        filename = name
    
    if filename is None:
      raise Exception('Configuration file is not exists')
    
    with open('./tests/config.json', 'r') as read_file:
      OPTS = json.load(read_file)
  
      mqtt_options = OPTS['mosquitto']
      options_watson = OPTS['watson_iot']
      options_db = OPTS['local_storage']
      options_dispatcher = OPTS['dispatcher']
  
      client_id = '%s_chariot_southbound_dispatcher' % uuid.uuid4()
  
      client = gmqtt.Client(client_id, clean_session=True)
      await client.connect(host=mqtt_options['host'], port=mqtt_options['port'], version=4)
  
      logger = LogDigester(options_dispatcher)
      logger.register_for_client(client)
      logger.set_up_local_storage(options_db)
      if options_watson['enabled']:
          logger.set_up_watson(options_watson)
  
      logger.subscribe(options_dispatcher['listen'], qos=2)
  
      for key, value in options_dispatcher['gateways_ids'].items():
          logger.subscribe(key, qos=2)
  
      await STOP.wait()
      await client.disconnect()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)
    
    loop.run_until_complete(main())
