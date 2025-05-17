import asyncio
import json
import time

import network
from machine import Pin

from microdot import Microdot

app = Microdot()

METRICS_TEMPLATE = """# HELP sepmon_pressure_depth Pico Temp in C
# TYPE sepmon_pressure_depth gauge
sepmon_pressure_depth {temperature}
"""

METRICS_PORT = 8080
LED = Pin("LED", machine.Pin.OUT)
TEMP_PIN = 4
TEMP_SENSOR = machine.ADC(TEMP_PIN)

with open("config") as f:
    CONFIG = json.load(f)
    print(CONFIG)

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
    while wlan.isconnected() == False:
        print("Waiting for connection...")
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

async def check_networking(wlan):
    while True:
        connected = wlan.isconnected()
        print(f"{time.time()} Network Check: {wlan}")
        if not connected:
            wlan = network_connect()
        await asyncio.sleep(300)

async def ok_blink():
    while True:
        blink()
        await asyncio.sleep(2)

@app.route('/metrics')
async def metrics(request):
    t = get_temperature()
    print(f"{time.time()} Temperature: {t}")
    return METRICS_TEMPLATE.format(temperature=t)

#read from A2D

if __name__ == "__main__":
    wlan = network_connect()
    asyncio.create_task(check_networking(wlan))
    asyncio.create_task(ok_blink())
    print(f"Serving metrics on port {METRICS_PORT}")
    app.run(port=METRICS_PORT)
