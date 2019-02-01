FROM python:3.6-alpine

WORKDIR /usr/src/app

# Bundle app source
COPY . .

RUN apk add gnupg gcc g++ make python3-dev libffi-dev openssl-dev gmp-dev && pip install pytest && python setup.py install
CMD ["python -m chariot_southbound_dispatcher.digester.logs"]
