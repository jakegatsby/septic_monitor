import asyncio
import gc
import json
import time
import math
import network
import machine

from microdot import Microdot, Response

app = Microdot()

STATE = {
    "current_metrics": {},
    "last_scraped_metrics": {},
}

METRICS_PORT = 8080
LED = machine.Pin("LED", machine.Pin.OUT)

# ADC Pins: GP26 (ADC0), GP27 (ADC1), GP28 (ADC2)
# Avoided GP24 (CYW43 SPI data line)
TEMP_PIN = 4  # Internal MicroPython ADC channel 4 for MCU temperature
TEMP_SENSOR = machine.ADC(TEMP_PIN)

CURRENT_PIN = 26  # GP26 / Physical Pin 31 (ADC0)
CURRENT_SENSOR = machine.ADC(CURRENT_PIN)

METRICS_TEMPLATE = """# HELP sepmon_pump_ac_current Pump AC current RMS
# TYPE sepmon_pump_ac_current gauge
sepmon_pump_ac_current {pump_ac_current}

# HELP sepmon_pump_ac_power Pump AC power live
# TYPE sepmon_pump_ac_power gauge
sepmon_pump_ac_power {pump_ac_power}

# HELP sepmon_pump_ac_state Pump running state
# TYPE sepmon_pump_ac_state gauge
sepmon_pump_ac_state {pump_state}

# HELP sepmon_pressure_sensor_temperature Pressure sensor temperature
# TYPE sepmon_pressure_sensor_temperature gauge
sepmon_pressure_sensor_temperature {temperature}
"""

with open("config") as f:
    CONFIG = json.load(f)


def blink():
    LED.value(not LED.value())


async def ok_blink():
    while True:
        blink()
        await asyncio.sleep(2)


async def error_blink():
    for _ in range(20):
        blink()
        await asyncio.sleep(0.08)


async def configure_networking():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(CONFIG["network"]["ssid"], CONFIG["network"]["password"])
    while not wlan.isconnected():
        syslog("Connecting to WLAN")
        error_blink()
        time.sleep(1)
    ifconfig = wlan.ifconfig()
    ip = CONFIG["network"]["ip"]
    wlan.ifconfig((ip, ifconfig[1], ifconfig[2], ifconfig[3]))
    wlan.config(pm=0xa11140)
    syslog(f"IP set to {ip}")

    while True:
        connected = wlan.isconnected()
        syslog(f"{time.time()} Network Check: {wlan}")
        if not connected:
            wlan = network_connect()
        await asyncio.sleep(300)


def get_temperature():
    adc_value = TEMP_SENSOR.read_u16()
    return round(adc_value, 1)


def get_ac_current():
    print("TODO")

def get_ac_power():
    print("TODO")

def get_pump_state():
    print("TODO")



async def poll_metrics():
    while True:
        # Measure current first so get_ac_power and get_pump_state can utilize it
        ac_current = get_ac_current()
        temp = get_temperature()

        STATE["current_metrics"] = {
            "temperature": get_temperature(),
            "pump_ac_current": get_ac_current(),
            "pump_ac_power": get_ac_power(),
            "pump_state": get_pump_state()
        }
        gc.collect()
        await asyncio.sleep(1)


@app.route("/metrics")
async def metrics(request):
    client_ip, client_port = request.client_addr
    syslog(f"Got /metrics request from {client_ip}")
    current_metrics = STATE.get("current_metrics")
    if not current_metrics:
        return Response("Metrics Not Ready", status_code=503)

    # FIXME - determine if pump on, if request is heartbeat, etc

    payload = METRICS_TEMPLATE.format(**current_metrics)
    STATE["last_scraped_metrics"] = current_metrics
    return Response(
        payload,
        headers={'Content-Type': 'text/plain; version=0.0.4'}
    )


async def main():
    asyncio.create_task(configure_networking())
    asyncio.create_task(ok_blink())
    asyncio.create_task(poll_metrics())
    await app.start_server(host='0.0.0.0', port=METRICS_PORT)


if __name__ == "__main__":
    asyncio.run(main())