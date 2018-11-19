#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import gmqtt
import pytest

import uuid

from chariot_base.tests import cleanup, Callbacks
from chariot_southbound_dispatcher.digester import LogDigester
from chariot_southbound_dispatcher.digester.logs import main

OPTS = json.load(open('tests/config.json', 'r'))
options = OPTS['mosquitto']

host = options['host']
port = options['port']
username = options['username']

topic = 'dispatcher'


@pytest.fixture()
async def init_clients():
    await cleanup(host, port, username)

    a_client = gmqtt.Client('%s_chariot_southbound_dispatcher' % uuid.uuid4(), clean_session=True)
    a_client.set_auth_credentials(username)

    b_client = gmqtt.Client('%s_chariot_southbound_dispatcher' % uuid.uuid4(), clean_session=True)
    b_client.set_auth_credentials(username)

    callback = LogDigester()
    callback.register_for_client(a_client)

    callback_b = Callbacks()
    callback_b.register_for_client(b_client)

    yield a_client, callback, b_client, callback_b

    await a_client.disconnect()
    await b_client.disconnect()


@pytest.mark.asyncio
async def test_basic(init_clients):
    a_client, callback, b_client, callback_b = init_clients

    await a_client.connect(host=host, port=port, version=4)
    await b_client.connect(host=host, port=port, version=4)

    callback.subscribe("%s/#" % topic, qos=2)
    callback.subscribe('iot-2/evt/nms_status/fmt/json', qos=2)
    callback_b.subscribe("privacy/#", qos=2)

    await asyncio.sleep(1)

    callback.publish("iot-2/evt/nms_status/fmt/json", '{"d": {"din0": 0}}')
    callback.publish("%s/iot-2/evt/nms_status/fmt/json" % topic, '{"d": {"din0": 0}}')
    callback.publish("%s/temperature" % topic, '{"din0": 1}')

    await asyncio.sleep(1)

    assert len(callback_b.messages) == 3

    callback.clear()


def test_get_sensor_info():
    logger = LogDigester()

    assert logger.get_sensor_info('temperature') == (1, 'temperature')
    assert logger.get_sensor_info('iot-2/evt/nms_status/fmt/json') == (0, '5410ec4d1601')


def test_set_up_watson():
    logger = LogDigester()
    options_watson = OPTS['iot']['client1']

    assert logger.connector is None
    logger.set_up_watson(options_watson)
    assert logger.connector is not None
    point = logger.point_factory.from_json_string('{"d": {"din0": 0}}', 'd')

    assert logger.store_to_global(point) is True


def test_set_up_local_storage():
    logger = LogDigester()
    options_db = OPTS['local_storage']

    assert logger.local_storage is None
    logger.set_up_local_storage(options_db)
    assert logger.local_storage is not None

    point = logger.point_factory.from_json_string('{"d": {"din0": 0}}', 'd')
    assert logger.store_to_local(point) is True


@pytest.mark.asyncio
async def test_main():
    await main()
