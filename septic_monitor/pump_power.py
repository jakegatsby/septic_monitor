# Monitors 120V AC powering pump

import logging
import os
import random
import signal
import sys
import time

import RPi.GPIO as GPIO
from prometheus_client import Gauge, start_http_server

log_fmt = "%(asctime)-28s %(module)-12s %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

METRICS_PORT = 8080
SLEEP_TIMEOUT = 60
PUMP_POWER_GPIO = 17
PUMP_POWER_GAUGE = Gauge("sepmon_pump_power", "sepmon_pump_power")


def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_POWER_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    signal.signal(signal.SIGINT, signal_handler)


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def get_pump_power():
    return GPIO.input(PUMP_POWER_GPIO)


if __name__ == "__main__":
    gpio_setup()
    start_http_server(METRICS_PORT)
    logger.info(f"Serving metrics on port {METRICS_PORT}")

    while True:
        pump_power = get_pump_power()
        logger.info(f"Pump Power (VAC): {pump_power}")
        PUMP_POWER_GAUGE.set(pump_power)
        time.sleep(SLEEP_TIMEOUT)
