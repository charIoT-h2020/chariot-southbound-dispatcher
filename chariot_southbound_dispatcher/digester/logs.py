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
from chariot_base.utilities import Tracer


class LogDigester(LocalConnector):
    def __init__(self, options):
        super(LogDigester, self).__init__()
        self.connector = None
        self.point_factory = DataPointFactory(options['database'], options['table'])
        self.local_storage = None
        self.tracer = None

        self.gateways_ids = options['gateways_ids']

    def on_message(self, client, topic, payload, qos, properties):
        span = self.start_span('on_message')
        span.set_tag('topic', topic)

        point = self.to_data_point(payload, topic)
        self.store_to_local(point, span)
        self.forward_to_engines(point, topic, span)
        self.store_to_global(point, span)

        self.close_span(span)

    def forward_to_engines(self, point, topic, child_span):
        span = self.start_span('forward_to_engines', child_span)
        sensor_type, sensor_id = self.get_sensor_info(topic)
        span.set_tag('sensor_type', sensor_type)
        span.set_tag('sensor_id', sensor_id)
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
        
        self.close_span(span)

    def store_to_local(self, point, child_span):
        span = self.start_span('store_to_local', child_span)
        if self.local_storage is not None:
            span.set_tag('table', point.table)
            result = self.local_storage.publish(point)
            self.close_span(span)
            return result
        self.close_span(span)

    def store_to_global(self, point, child_span):
        span = self.start_span('store_to_global', child_span)
        if self.connector is not None:
            self.close_span(span)
            return self.connector.publish(point)
        self.close_span(span)

    def start_span(self, id, child_span=None):
        if self.tracer is None:
            return

        if child_span is None:
            return self.tracer.tracer.start_span(id)
        else:
            return self.tracer.tracer.start_span(id, child_of=child_span)

    def close_span(self, span):
        if self.tracer is None:
            return
        span.finish()

    def set_up_watson(self, options):
        self.connector = WatsonConnector(options)

    def set_up_tracer(self, options):
        self.tracer = Tracer(options)
        self.tracer.init_tracer()

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
    print('Stoping....')
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
      options_tracer = OPTS['tracer']

      client_id = '%s_chariot_southbound_dispatcher' % uuid.uuid4()

      client = gmqtt.Client(client_id, clean_session=True)
      await client.connect(host=mqtt_options['host'], port=mqtt_options['port'], version=4)

      logger = LogDigester(options_dispatcher)
      logger.register_for_client(client)
      logger.set_up_local_storage(options_db)
      if options_tracer['enabled']:
          logger.set_up_tracer(options_tracer)
      if options_watson['enabled']:
          logger.set_up_watson(options_watson['client'])

      logger.subscribe(options_dispatcher['listen'], qos=2)

      for key, value in options_dispatcher['gateways_ids'].items():
          logger.subscribe(key, qos=2)

      print('Waiting message from Gateway')
      await STOP.wait()
      await client.disconnect()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)
    
    loop.run_until_complete(main())
    print('Stopped....')
