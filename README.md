# Chariot Southbound Dispatcher

Chariot southbound dispatcher micro-service


* Free software: Eclipse Public License 1.0

## How to use

### Build docker images

```
docker build --tag chariot_southbound_dispatcher .
```

Clean dangling images:

```
docker rmi $(docker images -f "dangling=true" -q)
```

### Send message to mqtt broker

```
mosquitto_pub -m '{"d": {"temperature": -10.0, "humidity": 40.0}}' -t dispatcher/temp:001
mosquitto_pub -m '{"d":{"din01":1,"din02":1,"din03":0,"din04":0,"din05":0,"din06":0,"din07":0,"din08":0,"din09":0,"din10":0,"din11":0,"din12":0,"din13":0,"din14":0,"din15":0,"din16":0,"ain01":2064,"ain02":0,"ain03":0,"ain04":0,"ain05":0,"ain06":0,"ain07":0,"ain08":0,"temperature":28.4,"humidity":44.1,"battery_voltage":9296}}' -t iot-2/evt/nms_status/fmt/json
```

## Features

* Get message from the gateway
* Log message to the local database instance
* Log message to the cloud database instance
* Forward message to the privacy engine

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
