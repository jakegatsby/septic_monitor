import asyncio
import json
import time

import network
import machine

from microdot import Microdot

app = Microdot()

STATE = {
    "current_metrics": {},
    "last_scraped_metrics": {},
}

METRICS_PORT = 8080
LED = machine.Pin("LED", machine.Pin.OUT)
TEMP_PIN = 4
TEMP_SENSOR = machine.ADC(TEMP_PIN)
PRESSURE_PIN = 28
PRESSURE_SENSOR = machine.ADC(PRESSURE_PIN)

METRICS_TEMPLATE = """# HELP sepmon_pressure_depth Pressure sensor depth reading
# TYPE sepmon_pressure_depth gauge
sepmon_pressure_depth {depth}

# HELP sepmon_pressure_sensor_temperature Pressure sensor temperature
# TYPE sepmon_pressure_sensor_temperature gauge
sepmon_pressure_sensor_temperature {temperature}
"""


with open("config") as f:
    CONFIG = json.load(f)


def error_blink():
    for _ in range(20):
        blink()
        time.sleep(0.08)


def blink():
    if LED.value() == 0:
        LED.on()
    else:
        LED.off()


def network_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(CONFIG["network"]["ssid"], CONFIG["network"]["password"])
    while not wlan.isconnected():
        print("Connecting to WLAN")
        error_blink()
        time.sleep(1)
    print("connected to wifi:")
    ifconfig = wlan.ifconfig()
    ip = CONFIG["network"]["ip"]
    wlan.ifconfig((ip, ifconfig[1], ifconfig[2], ifconfig[3]))
    print(f"IP set to {ip}")
    return wlan


def get_temperature():
    adc_value = TEMP_SENSOR.read_u16()
    volt = (3.3 / 65535) * adc_value
    return round(27 - (volt - 0.706) / 0.001721, 1)


def get_pressure_depth():
    """
    PRESSURE_SENSOR.read_u16() returns 0-65535 (12bit converted to 16bit)
    This function returns a value between 0 and 100
    """
    adc = (PRESSURE_SENSOR.read_u16() / 65535) * 100
    return round(adc)


async def check_networking(wlan):
    while True:
        connected = wlan.isconnected()
        print(f"{time.time()} Network Check: {wlan}")
        if not connected:
            wlan = network_connect()
        gc.collect()
        await asyncio.sleep(300)


async def ok_blink():
    while True:
        blink()
        await asyncio.sleep(2)


async def poll_metrics():
    while True:
        STATE["current_metrics"] = {
            "depth": get_pressure_depth(),
            "temperature": get_temperature()
        }
        gc.collect()
        await asyncio.sleep(10)


@app.route("/metrics")
async def metrics(request):
    current_metrics = STATE.get("current_metrics")
    if not current_metrics:
        return Response("", status_code=204)
    payload = METRICS_TEMPLATE.format(**current_metrics)
    STATE["last_scraped_metrics"] = current_metrics
    return Response(payload, headers={'Content-Type': 'text/plain; version=0.0.4'})


async def main():
    asyncio.create_task(check_networking(wlan))
    asyncio.create_task(ok_blink())
    asyncio.create_task(poll_metrics())
    await app.start_server(host='0.0.0.0', port=80)


if __name__ == "__main__":
    wlan = network_connect()
    asyncio.run(main())
