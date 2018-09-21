import paho.mqtt.client as mqtt

mqtt.Client.connected_flag = False


class Client(object):
    def __init__(self, client_od, broker):
        self.consumer = mqtt.Client(client_od)
        self.consumer.connect(broker)

        self.consumer.on_log = self.on_log
        self.consumer.on_message = self.on_message

    @staticmethod
    def on_message(client, userdata, message):
        pass

    @staticmethod
    def on_log(client, userdata, level, buf):
        pass

    def subscribe(self, topic):
        self.consumer.subscribe(topic)

    def publish(self, topic, msg):
        self.consumer.publish(topic, msg)

    def start(self, forever=True):
        if forever:
            self.consumer.loop_forever()
        else:
            self.consumer.loop_start()
