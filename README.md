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
mosquitto_pub -m '{"d": {"temperature": -10, "humidity": 40.0}}' -t dispatcher/urn:ngsi-ld:temp:001
```

## Features

* Log message to the local database instance
* Log message to the cloud database instance

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
