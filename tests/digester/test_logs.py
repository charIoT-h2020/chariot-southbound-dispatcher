# -*- coding: utf-8 -*-

"""Unit test package for chariot_southbound dispatcher."""

import uuid
import time
import unittest

from chariot_southbound_dispatcher.digester import LogDigester


def connect_to_mqtt_facade(topic):
    def connect(func):
        broker = 'localhost'
        client_id = '%s_chariot_southbound_dispatcher' % uuid.uuid4()

        logger = LogDigesterFacade(client_id, broker)
        logger.subscribe([
            (topic, 0)
        ])

        def func_wrapper(self, *args, **kwargs):
            result = func(self, logger, *args, **kwargs)
            time.sleep(.500)
            self.assertEqual(logger.errors, result)
            return result

        return func_wrapper
    return connect


class LogDigesterFacade(LogDigester):
    def __init__(self, client_od, broker):
        super(LogDigesterFacade, self).__init__(client_od, broker)
        self.errors = False

    def on_message(self, client, userdata, message):
        try:
            super(LogDigesterFacade, self).on_message(client, userdata, message)
        except Exception as err:
            print (str(err))
            self.errors = True

    def on_log(self, client, userdata, level, buf):
        super(LogDigesterFacade, self).on_log(client, userdata, level, buf)


class Message:
    def __init__(self, message, topic):
        self.retain = False
        self.payload = message.encode()
        self.topic = topic


class LogDigesterTest(unittest.TestCase):

    @connect_to_mqtt_facade('dispatcher/#')
    def test_to_data_point(self, logger):
        logger.to_data_point(Message('{"d": {}}', 'temperature'))
        logger.to_data_point(Message('{"d": {"din0": 0, "din1": 0, "din2": 0}}', 'iot-2/evt/nms_status/fmt/json'))
        self.assertRaises(Exception, logger.to_data_point, [Message('{}', 'temperature')])
        self.assertRaises(Exception, logger.to_data_point, [Message('0', 'temperature')])

        logger.start(False)
        return False

    @connect_to_mqtt_facade('dispatcher/#')
    def test_get_sensor_info(self, logger):
        self.assertEqual(logger.get_sensor_info('temperature'), (1, 'temperature'))
        self.assertEqual(logger.get_sensor_info('iot-2/evt/nms_status/fmt/json'), (0, '5410ec4d1601'))

        logger.start(False)
        return False

    @connect_to_mqtt_facade('dispatcher/#')
    def test_message_payload_from_panthora(self, logger):
        if logger is not None:
            logger.publish('dispatcher/temperature', '{"d": {"din0": 0, "din1": 0, "din2": 0}}')
            logger.start(False)
        return False

    @connect_to_mqtt_facade('dispatcher/#')
    def test_message_payload_correct(self, logger):
        if logger is not None:
            logger.publish('dispatcher/temperature', '{"d": {}}')
            logger.start(False)
        return False

    @connect_to_mqtt_facade('dispatcher/#')
    def test_message_payload_empty_json(self, logger):
        if logger is not None:
            logger.publish('dispatcher/temperature', '{}')
            logger.start(False)
        return True

    @connect_to_mqtt_facade('dispatcher/#')
    def test_message_payload_number(self, logger):
        if logger is not None:
            logger.publish('dispatcher/temperature', 0)
            logger.start(False)
        return True
