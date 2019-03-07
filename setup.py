#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'paho-mqtt',
    'influxdb',
    'cloudant',
    'ibmiotf',
    'jaeger-client',
    'chariot_base==0.6.3',
    'gmqtt'
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="George Theofilis",
    author_email='g.theofilis@clmsuk.com',
    classifiers=[
        'License :: OSI Approved :: Eclipse Public License 1.0',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    install_requires=requirements,
    license="EPL-1.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='chariot_southbound_dispatcher',
    name='chariot_southbound_dispatcher',
    packages=find_packages(include=[
        'chariot_southbound_dispatcher',
        'chariot_southbound_dispatcher.*'
    ]),
    entry_points={
          'console_scripts': [
              'logs = chariot_southbound_dispatcher.digester.logs:main'
          ]
    },
    scripts=['scripts/send_log.py'],
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://gitlab.com/chariot-h2020/chariot_southbound_dispatcher',
    version='0.5.4',
    zip_safe=False,
)
