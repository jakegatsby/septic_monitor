# Monitors 120VAC powering pump

import logging
import signal
import sys
import time

import RPi.GPIO as GPIO

from septic_monitor import logs, storage

logging.basicConfig(level=logging.INFO, format=logs.LOG_FMT)
logger = logging.getLogger(__name__)

SLEEP_TIMEOUT = 60
PUMP_AC_POWER_GPIO = 17


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_AC_POWER_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        pump_ac_state = GPIO.input(PUMP_AC_POWER_GPIO)
        logger.info("Pump state from pin: %s", pump_ac_state)
        storage.set_pump_ac_state(pump_ac_state)
        logger.info("Sleeping for %s seconds...", SLEEP_TIMEOUT)
        time.sleep(SLEEP_TIMEOUT)
