# -*- coding: utf-8 -*-
import json
import uuid
import gmqtt
import asyncio

from chariot_base.connector import LocalConnector


class MessageGenerator(LocalConnector):
    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


async def main():
    client_id = '%s_chariot_southbound_dispatcher' % uuid.uuid4()

    broker = '192.168.174.130'
    port = '1883'

    client = gmqtt.Client(client_id, clean_session=True)
    await client.connect(host=broker, port=port, version=4)

    log = {
        'd': {
            'temperature': -10.0,
            'humidity': 40.0
        }
    }
    callback = MessageGenerator()

    callback.register_for_client(client)

    callback.publish("dispatcher/device%s" % uuid.uuid4(), json.dumps(log))

    await asyncio.sleep(1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
