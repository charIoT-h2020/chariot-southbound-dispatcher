# -*- coding: utf-8 -*-

import os  
import uuid
import json
import gmqtt
import asyncio
import signal
import logging

from chariot_base.connector import WatsonConnector, LocalConnector
from chariot_base.model import DataPointFactory
from chariot_base.datasource import LocalDataSource
from chariot_base.utilities import Tracer, open_config_file


class LogDigester(LocalConnector):
    def __init__(self, options):
        super(LogDigester, self).__init__()
        self.connector = None
        self.point_factory = DataPointFactory(options['database'], options['table'])
        self.local_storage = None
        self.tracer = None

        self.gateways_ids = options['gateways_ids']
        self.engines = options['engines']

    def on_message(self, client, topic, payload, qos, properties):
        try:
            span = self.start_span('on_message')
            points = self.to_data_point(payload, topic)

            for point in points:
                point_span = self.start_span('handle_measurement', span)
                point_span.set_tag('topic', topic)
                point_span.set_tag('package_id', point.id)

                try:
                    self.store_to_local(point, point_span)
                    self.forward_to_engines(point, topic, point_span)
                    self.store_to_global(point, point_span)
                    point_span.set_tag('is_ok', True)
                except:
                    point_span.set_tag('is_ok', False)
                self.close_span(point_span)

            self.close_span(span)
        except:
            span.set_tag('is_ok', False)
            self.close_span(span)

    def forward_to_engines(self, point, topic, child_span):
        try:
            span = self.start_span('forward_to_engines', child_span)
            span.set_tag('sensor_id', point.sensor_id)
            span.set_tag('package_id', point.id)
            message_meta = {
                'package_id': point.id,
                'timestamp': point.timestamp,
                'value': point.message,
                'sensor_id': point.sensor_id
            }
            self.inject_to_message(span, message_meta)
            msg = json.dumps(message_meta)
            
            for engine in self.engines:
                logging.debug('Send message to %s engine: %s' % (engine, msg))
                self.publish(engine, msg)
            
            self.close_span(span)
        except:
            span.set_tag('is_ok', False)
            self.close_span(span)
            raise

    def store_to_local(self, point, child_span):
        result = False

        if self.local_storage is None:
            return result

        try:
            span = self.start_span('store_to_local', child_span)
            span.set_tag('package_id', point.id)
            result = self.local_storage.publish(point)
            span.set_tag('is_ok', result)
            self.close_span(span)
            return result
        except:
            span.set_tag('is_ok', False)
            self.close_span(span)
            raise

    def store_to_global(self, point, child_span):
        result = False

        if self.connector is None:
            return False

        try:
            span = self.start_span('store_to_global', child_span)            
            span.set_tag('package_id', point.id)
            result = self.connector.publish(point)
            span.set_tag('is_ok', result)
            self.close_span(span)
            return result
        except:
            span.set_tag('is_ok', False)
            self.close_span(span)
            raise

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
        points = self.point_factory.from_json_string(message)

        i = 0
        for point in points:
            point.id = str(point.id)
            if point.sensor_id is None:
                point.sensor_id = topic
            i = i + 1
        
        return points

    def get_sensor_info(self, topic):
        topic = topic.replace('dispatcher/', '')

        if topic in self.gateways_ids:
            return 0, self.gateways_ids[topic]
        else:
            return 1, topic


STOP = asyncio.Event()


def ask_exit(*args):
    logging.info('Stoping....')
    STOP.set()


async def main(args=None):
    opts = open_config_file()

    mqtt_options = opts.brokers.southbound
    options_watson = opts.watson_iot
    options_db = opts.local_storage
    options_dispatcher = opts.dispatcher
    options_tracer = opts.tracer
    
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

    logging.info('Waiting message from Gateway')
    await STOP.wait()
    await client.disconnect()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)
    
    loop.run_until_complete(main())
    logging.info('Stopped....')
