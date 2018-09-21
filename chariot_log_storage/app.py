# -*- coding: utf-8 -*-
from influxdb import InfluxDBClient

import datetime

from consumer import Client


class MessageLogger(Client):

    @staticmethod
    def on_message(client, userdata, message):
        print("(%s) message received(%s): %s  " % (message.topic, message.retain, message.payload.decode("utf-8")))
        json_body = [
            {
                "measurement": "value",
                "tags": {
                    "topic": "storage/urn:ngsi-ld:temp:001"
                },
                "time": datetime.datetime.now().isoformat(),
                "fields": {
                    "value": message.payload.decode("utf-8")
                }
            }
        ]
        db = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')
        db.write_points(json_body)
        if message.retain == 1:
            print("This is a retained message")

    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


if __name__ == '__main__':
    # Initialize connection to southbound
    broker = '172.18.1.2'
    client_id = 'chariot_log_storage'

    logger = MessageLogger(client_id, broker)

    logger.subscribe([
        ('dispatcher/#', 0)
    ])

    logger.start()
