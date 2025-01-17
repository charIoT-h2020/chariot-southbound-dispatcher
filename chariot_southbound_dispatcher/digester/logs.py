# -*- coding: utf-8 -*-

import os
import uuid
import json
import gmqtt
import asyncio
import signal
import logging
import requests
import uvloop

from chariot_base.datasource import LocalDataSource
from chariot_base.utilities import Tracer, open_config_file, HealthCheck, Topology
from chariot_base.model import Alert, DataPointFactory, UnAuthenticatedSensor, FirmwareUploadException, FirmwareUpdateStatus
from chariot_base.connector import WatsonConnector, LocalConnector, create_client
from chariot_southbound_dispatcher import __version__, __service_name__

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class LogDigester(LocalConnector):
    def __init__(self, options):
        super(LogDigester, self).__init__()
        self.options = options
        self.connector = None
        self.point_factory = DataPointFactory(
            options['database'], options['table'])
        self.firmware_upload_table = 'firmwareupload'
        self.point_factory.set_firmware_upload_table(self.firmware_upload_table)
        self.db = options['database']
        self.local_storage = None
        self.tracer = None
        self.northbound = None
        self.session = requests.Session()
        self.session.trust_env = False

        if 'health' in options:
            logging.info('Enabling health checks endpoints')
            self.health = HealthCheck(options['name']).inject_connector(self)
            self.healthTopic = options['health']['endpoint']

        self.gateways_ids = options['gateways_ids']
        self.engines = options['engines']

        if 'engines' not in options:
            raise Exception('engines is missing')

        self.topology = None
        if self.options['topology']['enabled']:
            self.topology = Topology(self.options['topology']['iotl_url'], self.tracer)
        self.topics = []

    def on_message(self, client, topic, payload, qos, properties):
        logging.debug(f'ERROR: {client._client_id}')
        if topic == self.healthTopic:
            self.health.do(payload)
            return

        span = self.start_span('on_message')
        try:
            logging.debug(f'{topic} {payload}')
            points = self.to_data_point(payload, topic, span)
            for point in points:
                point_span = self.start_span('handle_measurement', span)
                self.set_tag(point_span, 'topic', topic)
                self.set_tag(point_span, 'package_id', point.id)

                try:
                    self.store_to_local(point, point_span)
                    self.forward_to_engines(point, topic, point_span)
                    self.report_device(point, topic, point_span)
                    self.store_to_global(point, point_span)
                    self.set_tag(point_span, 'is_ok', True)
                except Exception as ex:
                    print(ex)
                    self.set_tag(point_span, 'is_ok', False)
                    self.error(span, ex, False)
                self.close_span(point_span)

            self.close_span(span)
        except Exception as ex:
            logging.error(ex)
            self.set_tag(span, 'is_ok', False)
            self.error(span, ex)

    def forward_to_engines(self, point, topic, child_span):
        try:
            span = self.start_span('forward_to_engines', child_span)
            self.set_tag(span, 'sensor_id', point.sensor_id)
            self.set_tag(span, 'package_id', point.id)
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
            self.set_tag(span, 'is_ok', False)
            self.close_span(span)
            raise

    def store_to_local(self, point, child_span):
        result = False

        if self.local_storage is None:
            return result

        try:
            span = self.start_span('store_to_local', child_span)
            self.set_tag(span, 'package_id', point.id)
            result = self.local_storage.publish(point)
            self.set_tag(span, 'is_ok', result)
            self.close_span(span)
            return result
        except:
            self.set_tag(span, 'is_ok', False)
            self.close_span(span)
            raise

    def store_to_global(self, point, child_span):
        result = False

        if self.connector is None:
            return False

        try:
            span = self.start_span('store_to_global', child_span)
            self.set_tag(span, 'package_id', point.id)
            result = self.connector.publish(point)
            self.set_tag(span, 'is_ok', result)
            self.close_span(span)
            return result
        except:
            self.set_tag(span, 'is_ok', False)
            self.close_span(span)
            raise

    def register_northbound(self, northbound):
        self.northbound = northbound

    def set_up_watson(self, options):
        self.connector = WatsonConnector(options)

    def set_up_tracer(self, options):
        self.tracer = Tracer(options)
        self.tracer.init_tracer()
        self.topology.tracer = self.tracer

    def set_up_local_storage(self, options):
        options['database'] = self.db
        self.local_storage = LocalDataSource(
            **options
        )

    def to_data_point(self, message, topic, span=None):
        try:
            points = self.point_factory.from_json_string(message)
        except UnAuthenticatedSensor as ex:
            alert_msg = 'Package from unauthenticated sensor \'%s\'' % ex.id
            alert = Alert('unauthenticated_sensor', alert_msg, 100)
            alert.sensor_id = ex.id
            self.northbound.publish('alerts', json.dumps(
                self.inject_to_message(span, alert.dict())))
            logging.debug(f'UnAuthenticatedSensor {ex.id}')
            return []
        except FirmwareUploadException as firmware_ex:
            alert_msg = f'Firmware update for sensor \'{firmware_ex.key}\' is failed'
            alert = Alert('firmware_upload_exception', alert_msg, 100)
            alert.sensor_id = firmware_ex.key
            self.northbound.publish('alerts', json.dumps(
                self.inject_to_message(span, alert.dict())))
            message = json.loads(message)
            old_name = list(message.keys())[0]
            message[firmware_ex.key] = message.pop(old_name)
            self.northbound.publish('firmware', json.dumps(message))
            logging.debug(f'FirmwareUploadException {firmware_ex.key}')
            point = FirmwareUpdateStatus(self.db, self.firmware_upload_table, firmware_ex.point)
            point.id = str(point.id)
            point.sensor_id = firmware_ex.key
            point.gateway = firmware_ex.gateway
            return [point]

        for point in points:
            point.id = str(point.id)
            if point.sensor_id is None:
                point.sensor_id = topic

            logging.debug(f'{type(point)} {type(point) == FirmwareUpdateStatus}')
            if type(point) == FirmwareUpdateStatus:
                logging.error(f'{json.dumps(point.sensor_id)} -> {json.dumps(point.message)}')
                message = { point.sensor_id: point.message }
                self.northbound.publish('firmware', json.dumps(message))
        return points

    def get_sensor_info(self, topic):
        topic = topic.replace('dispatcher/', '')

        if topic in self.gateways_ids:
            return 0, self.gateways_ids[topic]
        else:
            return 1, topic

    def report_device(self, point, topic, child_span):
        try:
            span = self.start_span('report_device', child_span)
            self.set_tag(span, 'sensor_id', point.sensor_id)
            self.set_tag(span, 'package_id', point.id)
            logging.debug(f'GW {point.gateway}')
            self.topology.report_new_sensor(point, span)

            self.close_span(span)
        except:
            self.set_tag(span, 'is_ok', False)
            self.close_span(span)
            raise

    def on_connect(self, client, flags, rc, properties=None):
        self.connected = True
        self.connack = (flags, rc, properties)
        logging.info(self.connack)

        if rc == 0:
            self.subscribe_to_topics()


    def set_topics(self, topics):
        self.topics = topics

    def subscribe_to_topics(self):
        subscriptions = []
        for topic in self.topics:
            subscriptions.append(gmqtt.Subscription(topic, qos=2))
        self.client.subscribe(subscriptions, subscription_identifier=1)
        logging.info('Waiting message from Gateway')

class NorthboundConnector(LocalConnector):
    def __init__(self):
        super(NorthboundConnector, self).__init__()
        self.engine = None


STOP = asyncio.Event()


def ask_exit(*args):
    logging.info('Stoping....')
    STOP.set()


async def main(args=None):
    opts = open_config_file()

    options_watson = opts.watson_iot
    options_db = opts.local_storage
    options_dispatcher = opts.dispatcher
    options_tracer = opts.tracer

    client_south = await create_client(opts.brokers.southbound, '_chariot_southbound_dispatcher')
    client_north = await create_client(opts.brokers.northbound, '_chariot_northbound_dispatcher')

    northbound = NorthboundConnector()
    northbound.register_for_client(client_north)

    logger = LogDigester(options_dispatcher)
    logger.register_for_client(client_south)
    logger.set_up_local_storage(options_db)
    logger.register_northbound(northbound)

    if options_tracer['enabled'] is True:
        service_name = f'{__service_name__}_{__version__}'
        options_tracer['service'] = service_name
        logging.info(f'Enabling tracing for service "{service_name}"')
        logger.set_up_tracer(options_tracer)
        northbound.inject_tracer(logger.tracer)
    if options_watson['enabled'] is True:
        logging.info('Enabling watson forwarding')
        logger.set_up_watson(options_watson['client'])

    topics = [options_dispatcher['listen']]
    for key, value in options_dispatcher['gateways_ids'].items():
        topics.append(key)

    logger.set_topics(topics)
    logger.subscribe_to_topics()

    await STOP.wait()
    await client_south.disconnect()
    await client_north.disconnect()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)

    loop.run_until_complete(main())
    logging.info('Stopped....')
