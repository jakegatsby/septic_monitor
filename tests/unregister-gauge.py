#!/usr/bin/env python

import time

from prometheus_client import CollectorRegistry, Gauge, start_http_server

REGISTRY = CollectorRegistry()
PUMP_CURRENT_GAUGE = Gauge("sepmon_pump_current", "sepmon_pump_current", registry=REGISTRY)

#start_http_server(port=8080, registry=REGISTRY)
start_http_server(port=8080)
time.sleep(1)
#REGISTRY.unregister(PUMP_CURRENT_GAUGE)