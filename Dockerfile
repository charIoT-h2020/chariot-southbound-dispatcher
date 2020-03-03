FROM registry.gitlab.com/chariot-h2020/chariot_base:latest

VOLUME ["/usr/src/app"]
WORKDIR /usr/src/app

# Bundle app source
COPY . .

RUN python setup.py install
CMD ["python", "./chariot_southbound_dispatcher/digester/logs.py"]
