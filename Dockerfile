FROM python:bullseye

COPY septic_monitor /opt/septic_monitor

COPY requirements.txt /tmp/requirements.txt

WORKDIR /opt/septic_monitor

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install build-essential python3-smbus rustc

RUN python -m pip install pip setuptools setuptools-rust wheel --upgrade && \
    CFLAGS=-fcommon python -m pip install -r /tmp/requirements.txt

