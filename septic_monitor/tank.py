import logging
import time
from time import sleep

import RPi.GPIO as GPIO

from septic_monitor import storage

logger = logging.getLogger(__name__)


GPIO.setwarnings(False)  # Ignore warning for now
GPIO.setmode(GPIO.BCM)  # Use Broadcom channel numbering
PIN_TRIGGER = 14
PIN_ECHO = 15
GPIO.setup(PIN_TRIGGER, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PIN_ECHO, GPIO.IN)
TIME_DIST_FACTOR = 17150


def main():
    while True:
        GPIO.output(PIN_TRIGGER, GPIO.HIGH)
        sleep(0.00002)
        GPIO.output(PIN_TRIGGER, GPIO.LOW)
        while GPIO.input(PIN_ECHO) == 0:
            pulse_start_time = time.time()
        while GPIO.input(PIN_ECHO) == 1:
            pulse_end_time = time.time()
        pulse_duration = pulse_end_time - pulse_start_time
        distance = pulse_duration * TIME_DIST_FACTOR
        storage.set_tank_level(distance)  # storage will ensure this is a correct level
        logger.info("Distance: %d cm", distance)
        time.sleep(storage.get_tank_level_poll())

if __name__ == "__main__":
    main()
