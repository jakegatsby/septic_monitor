import logging
from datetime import datetime

import pytz
from fastapi import FastAPI
from pydantic import BaseModel

from septic_monitor import logs
    
app = FastAPI()

logging.basicConfig(level=logging.INFO)

try:
    from septic_monitor import storage
except:
    logging.error("Import storage failed")

class RemoteTemperature(BaseModel):
    temperature: float


@app.get("/api/status/")
async def lastupdate():    
    return storage.status()
        

@app.get("/api/tank/level/")
async def get_tank_level():
    return storage.get_tank_level()


@app.get("/api/tank/level/{duration}/")
async def get_tank_level_duration(duration):
    levels = storage.get_tank_level(duration=duration)
    if not levels:
        return []
    return [{"x": l.timestamp, "y": l.value} for l in levels]


@app.get("/api/pump/amperage/")
async def get_pump_amperage():
    return storage.get_pump_amperage()


@app.get("/api/pump/amperage/{duration}/")
async def get_pump_amperage_duration(duration):
    amperages = storage.get_pump_amperage(duration=duration)
    if not amperages:
        return []
    return [{"x": l.timestamp, "y": l.value} for l in amperages]


@app.post("/api/remote/temperature/")
async def post_remote_temperature(temperature: RemoteTemperature):
    logging.info(temperature)
    return temperature

