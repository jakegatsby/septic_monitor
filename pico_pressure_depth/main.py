import asyncio
import gc
import json
import time

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

SYSLOG_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SYSLOG_TAG = "pico-pressure-depth"

with open("config") as f:
    CONFIG = json.load(f)

def syslog(message, severity=6, facility=16):
    """
    Sends an RFC 3164 compliant Syslog UDP message.
    Severity: 3=Error, 4=Warning, 6=Info, 7=Debug
    """
    pri = (facility * 8) + severity
    # Format: <PRI>TAG: MESSAGE
    packet = f"<{pri}>{CONFIG['network']['ip']} {SYSLOG_TAG}: {message}"

    try:
        SYSLOG_SOCK.sendto(packet.encode("utf-8"), (SYSLOG_IP, SYSLOG_PORT))
    except Exception as e:
        print(f"Failed to send syslog: {e}")


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
        for attempt in range(20):
            print("Connecting to Wi-Fi...")
                        if wlan.isconnected():
                print(f"Connected! IP set to {wlan.ifconfig()[0]}")
                break

            try:
                # Disable Wi-Fi power-saving mode to prevent dropped packets / high latency
                wlan.config(pm=0xa11140)
                wlan.ifconfig((ip, subnet, gateway, dns))
                wlan.connect(CONFIG["network"]["ssid"], CONFIG["network"]["password"])


                    blink()
                    await asyncio.sleep(0.5)
                else:
                    print("Wi-Fi connection attempt timed out.")
                    await error_blink()

            except Exception as e:
                print(f"Wi-Fi Error: {e}")
                await error_blink()

        STATE["wlan_is_connected"] = True
        await asyncio.sleep(15)


def get_temperature():
    adc_value = TEMP_SENSOR.read_u16()
    return round(adc_value, 1)


def get_pressure_depth():
    """
    PRESSURE_SENSOR.read_u16() returns 0-65535 (12bit converted to 16bit)
    This function returns a value between 0 and 100
    """
    adc = (PRESSURE_SENSOR.read_u16() / 65535) * 100
    return round(adc, 1)


async def poll_metrics():
    while True:
        try:
            STATE["current_metrics"] = {
                "depth": get_pressure_depth(),
                "temperature": get_temperature()
            }
        except Exception as e:
            STATE["current_metrics"] = {}
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
    await app.start_server(host='0.0.0.0', port=METRICS_PORT)


if __name__ == "__main__":
    asyncio.run(main())