import json
import time

import network
import requests
from machine import Pin

LED = Pin("LED", machine.Pin.OUT)
TEMP_PIN = 4
TEMP_SENSOR = machine.ADC(TEMP_PIN)

with open("config") as f:
    CONFIG = json.load(f)

API_IP = CONFIG["api"]["ip"]
API_PORT = CONFIG["api"]["port"]


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
    ip = wlan.ifconfig()[0]
    print(f"Connected on {ip}")


def read_temperature():
    adc_value = TEMP_SENSOR.read_u16()
    volt = (3.3 / 65535) * adc_value
    temperature = round(27 - (volt - 0.706) / 0.001721, 1)
    data = {
        "temperature": temperature,
    }
    post_url = f"http://{API_IP}:{API_PORT}/api/remote/temperature/"
    try:
        r = requests.post(
            url=post_url, json=data
        )
        r.close()
        print(f"[INFO] PICO temperature of {temperature} sent to {API_IP}:{API_PORT}")
        blink()
    except Exception as e:
        print(f"[ERROR] POST {post_url} failed: {str(e)}")
        error_blink()


def main():    
    network_connect()
    while True:        
        read_temperature()
        time.sleep(1)


if __name__ == "__main__":
    main()
