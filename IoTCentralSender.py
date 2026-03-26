import os
import asyncio
import configparser
import sys
import json
import random
import math

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from iotc.models import Property, Command

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "samples.ini"))

if config["DEFAULT"].getboolean("Local"):
    sys.path.insert(0, "src")

from iotc import (
    IOTCConnectType,
    IOTCLogLevel,
    IOTCEvents,
    Command,
    CredentialsCache,
    Storage,
)
from iotc.aio import IoTCClient

device_id = os.environ["DEVICE_ID"]
scope_id = os.environ["SCOPE_ID"]
key = os.environ["DEVICE_KEY"]

# Historical data settings
DAYS_OF_HISTORY = 4          # How many days back to start
INTERVAL_MINUTES = 30        # One reading every 30 minutes

class MemStorage(Storage):
    def retrieve(self):
        return None

    def persist(self, credentials):
        return None

model_id = None

async def on_props(prop: Property):
    print(f"Received {prop.name}:{prop.value}")
    return True

async def on_commands(command: Command):
    print("Received command {} with value {}".format(command.name, command.value))
    await command.reply()

async def on_enqueued_commands(command: Command):
    print("Received offline command {} with value {}".format(command.name, command.value))

client = IoTCClient(
    device_id,
    scope_id,
    IOTCConnectType.IOTC_CONNECT_DEVICE_KEY,
    key,
    storage=MemStorage(),
)
if model_id is not None:
    client.set_model_id(model_id)

client.set_log_level(IOTCLogLevel.IOTC_LOGGING_ALL)
client.on(IOTCEvents.IOTC_PROPERTIES, on_props)
client.on(IOTCEvents.IOTC_COMMAND, on_commands)
client.on(IOTCEvents.IOTC_ENQUEUED_COMMAND, on_enqueued_commands)


def generate_reading(ts: datetime) -> dict:
    """Generate realistic sensor values for a given timestamp."""
    # Use hour of day to simulate daily temperature cycle (cooler at night, warmer midday)
    hour = ts.hour + ts.minute / 60.0
    temp_base = 22 + 8 * math.sin(math.pi * (hour - 6) / 12)  # peaks ~18:00
    tempExternaC = round(temp_base + random.uniform(-2.0, 2.0), 1)

    # Humidity inversely correlated with temperature
    humedad_base = 75 - 1.2 * (tempExternaC - 22)
    humedadExternaPct = round(min(100.0, max(0.0, humedad_base + random.uniform(-5.0, 5.0))), 1)

    # Wind speed: light breeze with occasional gusts
    vientoMps = round(max(0.0, random.gauss(2.5, 1.5)), 1)

    # Rain: mostly 0, small chance of rain event
    if random.random() < 0.1:
        lluviaMm = round(random.uniform(0.5, 15.0), 1)
    else:
        lluviaMm = 0.0

    return {
        "tempExternaC": tempExternaC,
        "humedadExternaPct": humedadExternaPct,
        "vientoMps": vientoMps,
        "lluviaMm": lluviaMm,
    }


async def main():
    await client.connect()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=DAYS_OF_HISTORY)
    total_readings = DAYS_OF_HISTORY * 24 * (60 // INTERVAL_MINUTES)

    print(f"Sending {total_readings} readings from {start_time.isoformat()} to {now.isoformat()}")

    for i in range(total_readings):
        if client.is_connected():
            ts = start_time + timedelta(minutes=i * INTERVAL_MINUTES)
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")

            payload = generate_reading(ts)
            payload["$ts"] = ts_str  # Backdate the telemetry timestamp in IoT Central

            await client.send_telemetry(payload)
            print(f"[{i+1}/{total_readings}] {ts_str} -> {payload}")

        # Small delay to avoid IoT Hub throttling (max ~100 msg/s per device)
        await asyncio.sleep(0.3)

    print("Historical upload complete.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
