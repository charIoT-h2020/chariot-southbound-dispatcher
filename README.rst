======================
Chariot Southbound Dispatcher
======================

Chariot southbound dispatcher micro-service


* Free software: Eclipse Public License 1.0

Build docker images
--------

.. code:: bash
    docker build --tag chariot_southbound_dispatcher .

Clean dangling images:

.. code:: bash
  docker rmi $(docker images -f "dangling=true" -q)

Send message to mqtt broker
--------

.. code:: bash
  mosquitto_pub -m '{"d": {"temperature": -10, "humidity": 40.0}}' -t dispatcher/urn:ngsi-ld:temp:001

Features
--------

* Log message to the local database instance
* Log message to the cloud database instance

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
