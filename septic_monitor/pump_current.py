# Read pump AC current while pump is running

import logging
import signal
import sys
import time

import adafruit_ads1x15.ads1115 as ADS
import board
import busio
import RPi.GPIO as GPIO
from adafruit_ads1x15.analog_in import AnalogIn

from prometheus_client import Gauge, start_http_server

log_fmt = "%(asctime)-28s %(module)-12s %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

METRICS_PORT = 8080
PUMP_OFF_READING_INTERVAL: 300
PUMP_RUNNING_READING_INTERVAL: 30
V_TO_I_FACTOR = 6
PUMP_RUNNING_GPIO = 27
LED_GPIO = 26
PUMP_CURRENT_GAUGE = Gauge("sepmon_pump_current", "sepmon_pump_current")

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def pump_current_callback(channel):
    logger.info("Pump started running!")
    logger.info("{:>5}\t{:>5}\t{:>5}".format("-Raw-", "AC Voltage", "AC Current"))

    PUMP_STATE = 1
    PUMP_CURRENT_GAUGE.set(0.0)
    time.sleep(5)  #Delay start to eliminate surge current in pump motor reading

    while PUMP_STATE == 1:
        PUMP_STATE = GPIO.input(PUMP_RUNNING_GPIO)
        chan_current = chan.voltage * V_TO_I_FACTOR
        logger.info(
            "{:>5}\t{:>5.3f}\t{:>5.3f}".format(chan.value, chan.voltage, chan_current)
        )
        PUMP_CURRENT_GAUGE.set(chan_current)
        time.sleep(PUMP_RUNNING_READING_INTERVAL)

    PUMP_CURRENT_GAUGE.set(0)
    logger.info("Pump off, current = 0.0")


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_RUNNING_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(LED_GPIO, GPIO.OUT)

    GPIO.add_event_detect(
        PUMP_RUNNING_GPIO, GPIO.RISING, callback=pump_current_callback, bouncetime=50
    )

    signal.signal(signal.SIGINT, signal_handler)

    start_http_server(METRICS_PORT)

    logger.info(f"Serving metrics on port {METRICS_PORT}")
    logger.info(f"{PUMP_OFF_READING_INTERVAL=}")
    logger.info(f"{PUMP_RUNNING_READING_INTERVAL=}")

    count = 0
    while True:
        # set zero current every PUMP_OFF_READING_INTERVAL seconds if pump not running
        if count % PUMP_OFF_READING_INTERVAL == 0:
            count = 0
            if GPIO.input(PUMP_RUNNING_GPIO) == 0:
                logger.info("Pump off, current = 0.0")
                PUMP_CURRENT_GAUGE.set(0.0)
        time.sleep(1)
        count += 1
