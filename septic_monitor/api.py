import logging
import random
import time
from datetime import datetime


from prometheus_client import start_http_server, CollectorRegistry, Gauge, Summary

from septic_monitor import logs
    

logging.basicConfig(level=logging.INFO)

pico_temperature_gauge = Gauge("pico_temperature_gauge", "Pico Temperature")

GAUGES = set()

def get_gauge(name):
    return [g for g in GAUGES if str(g) == f"gauge:{name}"][0]


start_http_server(8000)
while True:
    pico_temperature_gauge.set(20)
    for i in range(50):
        #v = random.choice([0,0,0,0,0,0,0,0,0,0,1,1])
        v = random.choice([0])
        #v = random.choice([1])
        g_name = f"cm_networking_gauge_{i}"
        try:
            g = Gauge(g_name, f"CM Networking ({i})")
            GAUGES.add(g)
        except:
            g = get_gauge(g_name)
        g.set(v)
    time.sleep(10)
