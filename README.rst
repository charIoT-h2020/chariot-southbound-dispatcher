=============================
CharIoT Southbound Dispatcher
=============================

|epl|_

The southbound dispatcher, is responsible for capturing sensor data as it comes in from the PANTHORA gateway. This micro-service initially processes the incoming message, adds some metadata and persists the package’s content both in the local and the cloud storage. It also forwards the message to the IPSE engine. 

The metadata that the Southbound dispatcher adds to a package are:

* A unique identifier of the message in the context of the fog node;
* A timestamp

There is some more processing of the message depending on the topology of the network, like:

* Transformation of a raw sensor value to a format that is understandable by the engines
* Basic validation of the incoming values (datatype, range, etc.)

Features
--------

* Receive message from the gateway
* Store message to the local database instance
* Store message to the cloud database instance
* Forward message to the engine

Models
------

Gateway message
~~~~~~~~~~~~~~~

We expect messages from PANTHORA gateway in a JSON document.

The following example is a message from the gateway, it contains values from sensor connected via wire on the gateway.

.. code-block:: shell

    {
        "<gateway_mac_addres>": {
            "fixedIO": {
                "din01": 0,
                "din02": 0,
                "din03": 0,
                "din04": 0,
                "din05": 0,
                "din06": 0,
                "din07": 0,
                "din08": 0,
                "din09": 0,
                "din10": 0,
                "din11": 0,
                "din12": 0,
                "din13": 0,
                "din14": 0,
                "din15": 0,
                "din16": 0,
                "ain01": 2060,
                "ain02": 2045,
                "ain03": 1291,
                "ain04": 1554,
                "ain05": 1652,
                "ain06": 1777,
                "ain07": 1926,
                "ain08": 1417
            }
        }
    }

The next example is a message from authenticated sensor connected via WiFi.

.. code-block:: shell

    {
        "<gateway_mac_address>": {
            "wifi": {
            "wifiStatusCode": 0,
            "wifiStatusText": "Wifi online",
            "sensorData": {
                "sensorName": "Sensor01",
                "sensorStatusCode": 0,
                "sensorStatusText": "Sensor online",
                "sensorValues": [
                    {
                        "name": "Temperature",
                        "value": "18.2"
                    },
                    {
                        "name": "Humidity",
                        "value": "37"
                    },
                    {
                        "name": "BatteryVoltage",
                        "value": "8.3"
                    }
                    ]
                }
            }
        }
    }

The last example is a message from not authenticated sensor connected via WiFi.

.. code-block:: shell

    {
        "<gateway_mac_address>": {
            "wifi": {
              "wifiStatusCode": 0,
              "wifiStatusText": "wifi online",
              "sensorData": {
                "sensorName": "Sensor01",
                "sensorStatusCode": 2,
                "sensorStatusText": "Sensor without authentication"
              }
            }
        }
    }

Southbound Package Model
~~~~~~~~~~~~~~~~~~~~~~~~

The message format sent by southbound dispatcher is the following:

.. code-block:: shell

    {
        "package_id": "<unique-guid>",
        "timestamp": "2019-03-05T12:08:26.888375",
        "value": {
            "<metric1_id>": <metric1_value>, 
            "<metric2_id>": <metric2_value>
        }, 
        "sensor_id": "<gateway_mac_address>"
    }

Configuration
-------------

dispatcher.gateways_ids
    A list of different gateway send message to the Fog Node.

dispatcher.engines
    The dispatcher send each new message to the engine defined in this list.

dispatcher.database
    The name of database where the message are stored.

dispatcher.table
    The name of table where the message are stored.

dispatcher.listen
    The central topic the dispatcher listen for message.


How to use
----------

Build docker images
~~~~~~~~~~~~~~~~~~~
.. code-block:: shell

   $ docker build --tag chariot_southbound_dispatcher .

Clean dangling images:

.. code-block:: shell

   $ docker rmi $(docker images -f "dangling=true" -q)


Send message to mqtt broker
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    # Send example message as gateway did
    $ mosquitto_pub -m '{"11:ac:a2:1a:9d:d6": {"fixedIO": { "din01": 1, "din02": 0 }}}' -t iot-2/evt/nms_status/fmt/json

    # Send example message as gateway did
    $ mosquitto_pub -m '{"52:80:6c:75:c3:fd": {"wifi": {"wifiStatusCode": 0, "wifiStatusText": "Wifi online", "sensorData": {"sensorName": "Sensor01","sensorStatusCode": 0,"sensorStatusText": "Sensor online","sensorValues": [{"name": "Temperature","value": 18.2}]}}}}' -t iot-2/evt/nms_status/fmt/json

Features
--------

Credits
-------

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.


.. |epl| image:: https://img.shields.io/badge/License-EPL-green.svg
.. _epl: https://opensource.org/licenses/EPL-1.0