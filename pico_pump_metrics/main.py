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


@app.after_request
async def cleanup(request, response):
    gc.collect()
    return response


def blink():
    LED.value(not LED.value())


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
    # MicroPython internal MCU temperature sensor standard conversion
    return round(27 - (volt - 0.706) / 0.001721, 1)


def get_ac_current():
    """
    Samples over 40ms (~2 full cycles at 50Hz/60Hz).
    Assumes a 1.65V DC offset bias (mid-point = 32768 on 16-bit scale).
    """
    start = time.ticks_ms()
    max_diff = 0
    baseline = 32768  # Midpoint DC offset for biased AC current transducers

    while time.ticks_diff(time.ticks_ms(), start) < 40:
        val = CURRENT_SENSOR.read_u16()
        diff = abs(val - baseline)
        if diff > max_diff:
            max_diff = diff

    # Scale peak displacement to Amps, then convert Peak to RMS (RMS = Peak / sqrt(2))
    peak_amps = (max_diff / 32768) * 15
    rms_amps = peak_amps / math.sqrt(2)

    # Noise gate: filter out trace ADC fluctuations at zero load
    if rms_amps < 0.1:
        rms_amps = 0.0

    return round(rms_amps, 2)


def get_ac_power():
    # Power = V_rms * I_rms (Assuming 120V AC nominal for this metric)
    current = STATE["current_metrics"].get("pump_ac_current", 0)
    voltage = CONFIG.get("ac_voltage", 120)
    return round(current * voltage, 1)


def get_pump_state():
    # 1 if pump is pulling current above threshold, 0 if off
    current = STATE["current_metrics"].get("pump_ac_current", 0)
    return 1 if current > 0.5 else 0


async def ok_blink():
    while True:
        blink()
        await asyncio.sleep(2)


async def poll_metrics():
    while True:
        # Measure current first so get_ac_power and get_pump_state can utilize it
        ac_current = get_ac_current()
        temp = get_temperature()

        STATE["current_metrics"] = {
            "temperature": temp,
            "pump_ac_current": ac_current,
            "pump_ac_power": round(ac_current * CONFIG.get("ac_voltage", 120), 1),
            "pump_state": 1 if ac_current > 0.5 else 0
        }
        gc.collect()
        await asyncio.sleep(1)


@app.route("/metrics")
async def metrics(request):
    current_metrics = STATE.get("current_metrics")
    if not current_metrics:
        return Response("Metrics Not Ready", status_code=503)

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