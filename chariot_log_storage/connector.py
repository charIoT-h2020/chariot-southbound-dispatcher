import datetime
from multiprocessing import Process

import ibmiotf.gateway


class IOTPConnector(Process):

    def __init__(self):
        super(IOTPConnector, self).__init__()
        try:
            options = {
                "org": "xjwcy3",
                "type": "Gateway",
                "id": "5410ec4d1601",
                "auth-method": "token",
                "auth-token": "LeeuJKfdIlgOavNOZS"
              }
            self.iot_client = ibmiotf.gateway.Client(options)
            self.iot_client.connect()
        except ibmiotf.ConnectionException as e:
            print(e)

    def push_data(self, message):
        """

        :param message: message
        :return:
        """
        self.iot_client.publishGatewayEvent(event="message", msgFormat="json",
                                            data={'message': message,
                                                  'timestamp': datetime.datetime.now().isoformat()})
