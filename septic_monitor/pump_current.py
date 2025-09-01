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


from prometheus_client import CollectorRegistry, Gauge, start_http_server


log_fmt = "%(asctime)-28s %(module)-12s %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

METRICS_PORT = 8080
PROMETHEUS_SCRAPE_FREQUENCY = 5
PUMP_RUNNING_INTERVAL = 10
PUMP_OFF_INTERVAL = 600
V_TO_I_FACTOR = 6
PUMP_RUNNING_GPIO = 27
LED_GPIO = 26

REGISTRY = CollectorRegistry()
DUMMY = Gauge("sepmon_dummy", "sepmon_dummy", registry=REGISTRY)  # FIXME
PUMP_CURRENT_GAUGE = Gauge("sepmon_pump_current", "sepmon_pump_current", registry=REGISTRY)

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
    register_gauge(PUMP_CURRENT_GAUGE)
    PUMP_CURRENT_GAUGE.set(0.0)
    # Delay start to eliminate surge current in pump motor reading
    # This must also be greater than the prometheus scrape frequency
    time.sleep(PROMETHEUS_SCRAPE_FREQUENCY * 2)

    while PUMP_STATE == 1:
        PUMP_STATE = GPIO.input(PUMP_RUNNING_GPIO)
        chan_current = chan.voltage * V_TO_I_FACTOR
        logger.info(
            "{:>5}\t{:>5.3f}\t{:>5.3f}".format(chan.value, chan.voltage, chan_current)
        )
        PUMP_CURRENT_GAUGE.set(chan_current)
        time.sleep(PUMP_RUNNING_INTERVAL)

    PUMP_CURRENT_GAUGE.set(0)
    logger.info("Pump off, current = 0.0")
    time.sleep(PROMETHEUS_SCRAPE_FREQUENCY * 2)
    unregister_gauge(PUMP_CURRENT_GAUGE)

def register_gauge(gauge):
    try:
        REGISTRY.register(gauge)
    except ValueError as e:
        if "Duplicated" in str(e):
            logger.info(f"{gauge} already registered")

def unregister_gauge(gauge):
    try:
        REGISTRY.unregister(gauge)
    except KeyError as e:
        logger.info(f"{gauge} already unregistered")


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_RUNNING_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(LED_GPIO, GPIO.OUT)

    GPIO.add_event_detect(
        PUMP_RUNNING_GPIO, GPIO.RISING, callback=pump_current_callback, bouncetime=50
    )

    signal.signal(signal.SIGINT, signal_handler)

    start_http_server(METRICS_PORT, registry=REGISTRY)

    logger.info(f"Serving metrics on port {METRICS_PORT}")

    while True:
        register_gauge(PUMP_CURRENT_GAUGE)
        logger.info("Registered PUMP_CURRENT_GAUGE")
        PUMP_CURRENT_GAUGE.set(0)
        logger.info(f"Sleeping {PROMETHEUS_SCRAPE_FREQUENCY * 2}s to allow prometheus to scrape 0 value...")
        time.sleep(PROMETHEUS_SCRAPE_FREQUENCY * 2)
        unregister_gauge(PUMP_CURRENT_GAUGE)
        logger.info("Unregistered PUMP_CURRENT_GAUGE")
        logger.info(f"Sleeping {PUMP_OFF_INTERVAL}s...")
        time.sleep(PUMP_OFF_INTERVAL)
