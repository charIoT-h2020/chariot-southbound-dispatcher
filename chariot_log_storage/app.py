# -*- coding: utf-8 -*-
import base64

import paho.mqtt.client as mqtt

mqtt.Client.connected_flag = False


def on_message(client, userdata, message):
    print("(%s) message received(%s): %s  " % (message.topic, message.retain, message.payload.decode("utf-8")))
    if message.retain == 1:
        print("This is a retained message")


def on_log(client, userdata, level, buf):
    print("log: ", buf)


# Initialize connection to southbound
broker = '172.18.1.2'
consumer = mqtt.Client('chariot_log_storage')
consumer.connect(broker)

consumer.on_log = on_log
consumer.on_message = on_message

consumer.subscribe([
    ('storage/#', 0)
])

consumer.loop_forever()
