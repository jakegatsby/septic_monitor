import logging
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.errors import DuplicateTable
import pytz
from attr import attrib, attrs

from septic_monitor import logs

logging.basicConfig(level=logging.INFO, format=logs.LOG_FMT)
logger = logging.getLogger(__name__)

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

while True:
    time.sleep(5)
    p = subprocess.run(
        ["pg_isready", "-h", POSTGRES_HOST, "-U", POSTGRES_USER, "-d", POSTGRES_DB],
        capture_output=True,
    )
    if p.returncode == 0:
        break
    logger.warning("Database not ready...")


CONN = psycopg2.connect(
    f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
)


@attrs
class TankLevel:
    timestamp = attrib()
    value = attrib()
    table = "tank_level"


@attrs
class PumpAmperage:
    timestamp = attrib()
    value = attrib()
    table = "pump_amperage"


@attrs
class PumpAcState:
    timestamp = attrib()
    value = attrib()
    table = "pump_ac_state"


@attrs
class DiskUsage:
    timestamp = attrib()
    value = attrib()
    table = "disk_usage"


for data_type in (TankLevel, PumpAmperage, PumpAcState, DiskUsage):
    with CONN.cursor() as cursor:
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {data_type.table} (time TIMESTAMPTZ NOT NULL, value DOUBLE PRECISION);"
            )
        except Exception as e:
            print(e)
        finally:
            CONN.commit()

    with CONN.cursor() as cursor:
        try:
            cursor.execute(f"SELECT create_hypertable('{data_type.table}', 'time');")
        except Exception as e:
            print(e)
        finally:
            CONN.commit()


BUCKETS = {
    "hour": "1 minutes",
    "day": "1 minutes",
    "week": "5 minutes",
    "month": "1 hours",
}


# hrs, days, weeks
DURATION_TO_ARGS = {
    "hour": (1, 0, 0),
    "day": (0, 1, 0),
    "week": (0, 0, 1),
    "month": (0, 0, 4),
}


def get_ts_data(data_type, duration=None):
    if duration is None:
        with CONN.cursor() as cursor:
            cursor.execute(
                f"SELECT time, value FROM {data_type.table} ORDER BY time DESC LIMIT 1"
            )
            return data_type(*cursor.fetchone())
    hours, days, weeks = DURATION_TO_ARGS[duration]
    start = datetime.now(pytz.UTC) - timedelta(hours=hours, days=days, weeks=weeks)
    with CONN.cursor() as cursor:
        cursor.execute(
            f"SELECT time_bucket(%s, time) AS bucket, max(value) FROM {data_type.table} WHERE time > %s GROUP BY bucket ORDER BY bucket ASC",
            (BUCKETS[duration], start),
        )
        return [data_type(row[0], row[1]) for row in cursor.fetchall()]


def set_ts_data(data_type, value):
    with CONN.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {data_type.table} (time, value) VALUES (now(), %s)", (value,)
        )
    CONN.commit()


def set_tank_level(level):
    level = 0 - abs(level)
    set_ts_data(TankLevel, level)
    logger.info("Set tank level: %s", level)


def get_tank_level(duration=None):
    if duration is None:
        return TankLevel(datetime.now(), random.randint(-20, -7))  # FIXME
    return get_ts_data(TankLevel, duration=duration)


def get_tank_level_warn():
    return int(0 - int(os.environ["TANK_LEVEL_WARN"]))


def set_pump_amperage(amperage):
    set_ts_data(PumpAmperage, amperage)
    logger.info("Set amperage: %s", amperage)


def get_pump_amperage(duration=None):
    return get_ts_data(PumpAmperage, duration=duration)


def set_pump_ac_state(state):
    state = int(state)
    set_ts_data(PumpAcState, state)
    logger.info("Set pump AC state: %s", state)


def get_pump_ac_state():
    ac_state = get_ts_data(PumpAcState, duration=None)
    ac_state.value = int(ac_state.value)
    return ac_state


def set_disk_usage(usage):
    set_ts_data(DiskUsage, usage)
    logger.info("Set disk usage: %s", usage)


def get_disk_usage():
    return get_ts_data(DiskUsage, duration=None)


def status(short=False):
    info = []
    warn = []

    try:
        tank_level = get_tank_level()
        tank_level_warn = get_tank_level_warn()
        if tank_level.value > tank_level_warn:
            msg = "LVL WARN!" if short else "Tank Level Exceeded Max!"
            warn.append(msg)
        else:
            msg = "LVL OK" if short else "Tank Level OK"
            info.append(msg)
    except Exception as e:
        logger.error("Error getting level data: %s", e)
        msg = "LVL?" if short else "Tank Level Data Unavailable"
        warn.append(msg)

    try:
        if int(get_pump_ac_state().value) == 1:
            msg = "PWR OK" if short else "Pump Power OK"
            info.append(msg)
        else:
            msg = "PWR LOSS!" if short else "Pump Power Loss!"
            warn.append(msg)
    except Exception as e:
        logger.error("Error getting AC state: %s", e)
        msg = "PWR?" if short else "Pump Power State Unavailable!"
        warn.append(msg)

    total, used, free = shutil.disk_usage(".")
    used_percent = int(used / total * 100)
    if used_percent > 90:
        msg = "HD WARN!" if short else "Disk Usage Exceeded 90%!"
        warn.append(msg)
    else:
        msg = "HD OK" if short else f"Disk Usage OK ({used_percent}% used)"
        info.append(msg)

    return {
        "info": sorted(info),
        "warn": sorted(warn),
    }
