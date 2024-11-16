import logging
import os
import struct
import time
from time import sleep

import serial

from septic_monitor import storage

logger = logging.getLogger(__name__)


NUM_READINGS = 30
READ_TIMEOUT = 1
POLL_INTERVAL = int(os.environ["TANK_LEVEL_POLL"]) * 60

SER = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1,
)


def get_distance():
    distances = list()
    for i in range(NUM_READINGS):
        SER.write(b"\x55")  # request data
        frame = SER.read(4)  # read a 4 byte frame
        header, high, low, checksum = struct.unpack("BBBB", frame)
        if header != 0xFF:
            logger.error("Invalid frame header: 0x%x", header)
            continue
        distance = (high << 8) + low
        chechsum_calculated = (header + high + low) & 0xFF
        if chechsum_calculated != checksum:
            logger.error(
                "Invalid checksum: 0x%x != 0x%x", chechsum_calculated, checksum
            )
        distances.append(distance)
        time.sleep(READ_TIMEOUT)
    average_distance = sum(sorted(distances)[5:-5]) / (NUM_READINGS - 10)
    return average_distance


def main():
    while True:
        distance = get_distance() / 10.0
        storage.set_tank_level(distance)  # storage will ensure this is a correct level
        logger.info("Distance: %d cm", distance)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
