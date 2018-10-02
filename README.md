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
```

## Features

* Get message from the gateway
* Log message to the local database instance
* Log message to the cloud database instance
* Forward message to the privacy engine

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
