import asyncio
import gc
import json
import time
import usocket as socket
import network
import machine
import ssd1306

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

ALARM_PIN = 16  # Connected to external audible alarm
ALARM_LEVEL = 60  # Tank level over 60 cm)
ALARM_CONDITION = machine.Pin(ALARM_PIN, machine.Pin.OUT)

try:
    i2c = machine.I2C(1, scl=machine.Pin(3), sda=machine.Pin(2), freq=400000)
    OLED = ssd1306.SSD1306_I2C(128, 64, i2c)
except Exception as e:
    OLED = False

METRICS_TEMPLATE = """# HELP sepmon_pressure_depth Pressure sensor depth reading
# TYPE sepmon_pressure_depth gauge
sepmon_pressure_depth {depth}

# HELP sepmon_pressure_sensor_temperature Pressure sensor temperature
# TYPE sepmon_pressure_sensor_temperature gauge
sepmon_pressure_sensor_temperature {temperature}
"""


with open("config") as f:
    CONFIG = json.load(f)

try:
    SYSLOG_IP = CONFIG["syslog"]["ip"]
    SYSLOG_PORT = CONFIG["syslog"]["port"]
    SYSLOG_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SYSLOG_TAG = "pico-pressure-depth"
    SYSLOG = True
except Exception as e:
    print(f"Unable to get syslog config")
    SYSLOG = False


def log(message, severity=6, facility=16):
    """
    Sends an RFC 3164 compliant Syslog UDP message.
    Severity: 3=Error, 4=Warning, 6=Info, 7=Debug
    """
    if not SYSLOG:
        print(message)

    pri = (facility * 8) + severity
    # Format: <PRI>TAG: MESSAGE
    packet = f"<{pri}>{CONFIG['network']['ip']} {SYSLOG_TAG}: {message}"

    try:
        SYSLOG_SOCK.sendto(packet.encode("utf-8"), (SYSLOG_IP, SYSLOG_PORT))
    except Exception as e:
        print(f"Failed to send syslog: {e}")
        print(message)


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
    init = True
    while True:
        if init:
            log(f"Initializing Networking")
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(CONFIG["network"]["ssid"], CONFIG["network"]["password"])
            while not wlan.isconnected():
                log("Connecting to WLAN")
                if OLED:
                    OLED.fill(0)
                    OLED.text("Connecting", 0, 0)
                    OLED.show()
                error_blink()
                time.sleep(1)
            ifconfig = wlan.ifconfig()
            ip = CONFIG["network"]["ip"]
            wlan.ifconfig((ip, ifconfig[1], ifconfig[2], ifconfig[3]))
            wlan.config(pm=0xA11140)
            if OLED:
                OLED.fill(0)
                OLED.text("Connected", 0, 0)
                OLED.text(f"{ip}", 0, 16)
                OLED.show()
            log(f"IP set to {ip}")

        if wlan.isconnected():
            log("Networking is connected")
            log(f"Chip tempurature is {get_temperature()} °C.")
            await asyncio.sleep(300)

        init = False if wlan.isconnected() else True


def get_temperature():
    conversion_factor = 3.3 / 65535
    reading = TEMP_SENSOR.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    if OLED:
        OLED.text(f"CPU: {temperature} C", 0, 32)
        OLED.show()
    return round(temperature, 1)


def get_pressure_depth():
    """
    PRESSURE_SENSOR.read_u16() returns 0-65535 (12bit converted to 16bit)
    This function returns a value between 0 and 100
    """
    adc = (PRESSURE_SENSOR.read_u16() / 65535) * 100
    """
    # Overwrite a specific line by drawing a black rectangle over it
    # Parameters: fill_rect(x, y, width, height, color)
    # Setting color to 0 fills it with black (clearing that specific area or whole line)
    """
    if OLED:
        OLED.fill_rect(48, 48, 36, 10, 0)
        OLED.text(f"Depth:{adc:.1f} cm", 0, 48)
        OLED.show()
    if adc >= ALARM_LEVEL:
        ALARM_CONDITION.value(1)  # Set pin HIGH
        log(f"Level over limit: {adc} >= {ALARM_LEVEL}")
    else:
        ALARM_CONDITION.value(0)  # Set or keep pin LOW
        log(f"Level OK: {round(adc, 1)} < {ALARM_LEVEL}")
    return round(adc, 1)


async def poll_metrics():
    while True:
        try:
            STATE["current_metrics"] = {"depth": get_pressure_depth(), "temperature": get_temperature()}
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
    return Response(payload, headers={"Content-Type": "text/plain; version=0.0.4"})


async def main():
    if not OLED:
        log("OLED is not available")
    asyncio.create_task(configure_networking())
    asyncio.create_task(ok_blink())
    asyncio.create_task(poll_metrics())
    await app.start_server(host="0.0.0.0", port=METRICS_PORT)


if __name__ == "__main__":
    asyncio.run(main())
