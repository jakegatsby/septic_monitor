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


@app.after_request
async def cleanup(request, response):
    gc.collect()
    return response


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

    ip = CONFIG["network"]["ip"]
    subnet = CONFIG["network"].get("subnet", "255.255.255.0")
    gateway = CONFIG["network"].get("gateway", "192.168.1.1")
    dns = CONFIG["network"].get("dns", "192.168.1.1")

    while True:
        if not wlan.isconnected():
            print("Connecting to Wi-Fi...")
            try:
                # Disable Wi-Fi power-saving mode to prevent dropped packets / high latency
                wlan.config(pm=0xa11140)
                wlan.ifconfig((ip, subnet, gateway, dns))
                wlan.connect(CONFIG["network"]["ssid"], CONFIG["network"]["password"])

                # Connection attempt loop with 10-second timeout
                for _ in range(20):
                    if wlan.isconnected():
                        print(f"Connected! IP set to {wlan.ifconfig()[0]}")
                        break
                    blink()
                    await asyncio.sleep(0.5)

                if not wlan.isconnected():
                    print("Wi-Fi connection attempt timed out.")
                    await error_blink()

            except Exception as e:
                print(f"Wi-Fi Error: {e}")
                await error_blink()

        # Poll Wi-Fi status every 15 seconds
        await asyncio.sleep(15)


def get_temperature():
    adc_value = TEMP_SENSOR.read_u16()
    volt = (3.3 / 65535) * adc_value
    return round(27 - (volt - 0.706) / 0.001721, 1)  # covert internal MCU temp to outside temp


def get_pressure_depth():
    """
    PRESSURE_SENSOR.read_u16() returns 0-65535 (12bit converted to 16bit)
    This function returns a value between 0 and 100
    """
    adc = (PRESSURE_SENSOR.read_u16() / 65535) * 100
    return round(adc, 1)


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
        return Response("Metrics Not Ready", status_code=503)
    payload = METRICS_TEMPLATE.format(**current_metrics)
    STATE["last_scraped_metrics"] = current_metrics
    return Response(payload, headers={'Content-Type': 'text/plain; version=0.0.4'})


async def main():
    asyncio.create_task(configure_networking())
    asyncio.create_task(ok_blink())
    asyncio.create_task(poll_metrics())
    await app.start_server(host='0.0.0.0', port=80)


if __name__ == "__main__":
    wlan = network_connect()
    asyncio.run(main())
