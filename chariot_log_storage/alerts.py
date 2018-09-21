# -*- coding: utf-8 -*-
from influxdb import InfluxDBClient

import datetime

from consumer import Client


class MessageLogger(Client):

    @staticmethod
    def on_message(client, userdata, message):
        msg, severity = message.payload.decode("utf-8").split(',')
        json_body = [
            {
                "measurement": "alert",
                "tags": {
                    "topic": "urn:ngsi-ld:temp:001"
                },
                "time": datetime.datetime.now().isoformat(),
                "fields": {
                    "severity": severity,
                    "msg": msg
                }
            }
        ]
        db = InfluxDBClient('localhost', 8086, 'root', 'root', 'fog_alerts')
        db.write_points(json_body)
        if message.retain == 1:
            print("This is a retained message")

    @staticmethod
    def on_log(client, userdata, level, buf):
        print("log: ", buf)


if __name__ == '__main__':
    # Initialize connection to northbound
    broker = '172.18.1.3'
    client_id = 'chariot_log_alert'

    logger = MessageLogger(client_id, broker)

    logger.subscribe([
        ('alerts/#', 0)
    ])

    logger.start()
