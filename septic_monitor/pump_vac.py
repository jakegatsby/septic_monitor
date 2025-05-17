# Monitors 120V AC powering pump

import logging
import os
import random
import signal
import sys
import time

log_fmt = '%(asctime)-28s %(module)-12s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except Exception as e:
    logger.error("Could not import RPi.GPIO")

from prometheus_client import start_http_server, Gauge

METRICS_PORT = 8080
SLEEP_TIMEOUT = 60
PUMP_VAC_GPIO = 17
PUMP_VAC_GAUGE = Gauge('sepmon_pump_vac', 'sepmon_pump_vac')

def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_VAC_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    signal.signal(signal.SIGINT, signal_handler)

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def get_pump_vac():
    if os.getenv("DEVMODE", False):
        logger.warning("DEVMODE")
        return random.random()
    else:
        return GPIO.input(PUMP_VAC_GPIO)

if __name__ == "__main__":
    if not os.getenv("DEVMODE", False):
        gpio_setup()

    start_http_server(METRICS_PORT)
    logger.info(f"Serving metrics on port {METRICS_PORT}")

    while True:
        pump_vac = get_pump_vac()
        logger.info(f"Pump V AC: {pump_vac}")
        PUMP_VAC_GAUGE.set(pump_vac)
        time.sleep(SLEEP_TIMEOUT)
