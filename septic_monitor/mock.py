import io
import itertools
import json
import logging
import random
import sys
import time
from datetime import datetime, timedelta, timezone

import boto3
import numpy as np
from scipy import signal

#from septic_monitor import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


S3 = boto3.resource('s3')


def back_data():
    t = datetime.now()
    for i in range(60):
        t = t - timedelta(days=i)
        storage.set_tank_level(40 - (4 * t.weekday()))


def main():
    if "backdata" in sys.argv:
        back_data()

    while True:
        #storage.set_tank_level(40 - (4 * datetime.now().weekday()))
        #storage.set_pump_amperage(random.choice(
        #    [0,] * 30 + [random.choice(range(11, 13)),]
        #))
        messages = []
        warnings = []

        tank_level = 0 - random.randint(10,30)
        if tank_level > -20:
            warnings.append(f"Tank Level: {tank_level} cm")
        else:
            messages.append(f"Tank Level: {tank_level} cm")

        disk_usage = random.randint(80,100)
        if disk_usage > 90:
            warnings.append(f"Disk Usage: {disk_usage}%")
        else:
            messages.append(f"Disk Usage: {disk_usage}%")

        status = {
          "timestamp": int(datetime.now(timezone.utc).timestamp()),
          "messages": messages,
          "warnings": warnings,
        }
        logger.info(status)
        s_io = io.BytesIO(json.dumps(status).encode())
        S3.meta.client.upload_fileobj(s_io, 'septic-monitor', 'status.json', ExtraArgs={'ACL':'public-read'})
        with open("dashboard/status.json", "w") as f:
            f.write(json.dumps(status))
        s_min = random.choice([5] * 4 + [12])
        time.sleep(60 * s_min)


if __name__ == "__main__":
    main()
