# -*- coding: utf-8 -*-

"""Unit test package for chariot_southbound dispatcher."""

import uuid
import time
import unittest

from chariot_southbound_dispatcher.digester import LogDigester


def connect_to_mqtt_facade(func):
    broker = 'localhost'
    client_id = '%s_chariot_southbound_dispatcher' % uuid.uuid4()

    logger = LogDigesterFacade(client_id, broker)
    logger.subscribe([
        ('dispatcher/#', 0)
    ])

    def func_wrapper(self, *args, **kwargs):
        result = func(self, logger, *args, **kwargs)
        time.sleep(.500)
        self.assertEqual(logger.errors, result)
        return result

    return func_wrapper


class LogDigesterFacade(LogDigester):
    def __init__(self, client_od, broker):
        super(LogDigesterFacade, self).__init__(client_od, broker)
        self.errors = False

    def on_message(self, client, userdata, message):
        try:
            super(LogDigesterFacade, self).on_message(client, userdata, message)
        except Exception as err:
            self.errors = True

    def on_log(self, client, userdata, level, buf):
        pass


class Message:
    def __init__(self, message, topic):
        self.retain = False
        self.payload = message.encode()
        self.topic = topic


class LogDigesterTest(unittest.TestCase):

    @connect_to_mqtt_facade
    def test_to_data_point(self, logger):
        logger.to_data_point(Message(u'{"d": {}}', 'temperature'))
        self.assertRaises(Exception, logger.to_data_point, [Message(u'{}', 'temperature')])
        self.assertRaises(Exception, logger.to_data_point, [Message(u'{}', 'temperature')])

        logger.start(False)
        return True

    @connect_to_mqtt_facade
    def test_message_payload_correct(self, logger):
        if logger is not None:
            logger.publish('dispatcher/temperature', '{"d": {}}')
            logger.start(False)
        return False

    @connect_to_mqtt_facade
    def test_message_payload_empty_json(self, logger):
        if logger is not None:
            logger.publish('dispatcher/temperature', '{}')
            logger.start(False)
        return True

    @connect_to_mqtt_facade
    def test_message_payload_number(self, logger):
        if logger is not None:
            logger.publish('dispatcher/temperature', 0)
            logger.start(False)
        return True
