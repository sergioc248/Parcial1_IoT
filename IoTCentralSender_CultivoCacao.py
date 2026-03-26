import os
import asyncio
import configparser
import sys
import random
import math

from datetime import datetime, timezone
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

device_id = os.environ["CACAO_DEVICE_ID"]
scope_id = os.environ["CACAO_SCOPE_ID"]
key = os.environ["CACAO_DEVICE_KEY"]

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
    # Cacao optimal range: 18-32°C, mild daily cycle
    hour = ts.hour + ts.minute / 60.0
    temp_base = 25 + 4 * math.sin(math.pi * (hour - 6) / 12)
    tempC = round(temp_base + random.uniform(-1.5, 1.5), 1)

    # High humidity environment (70-90%)
    humedad_base = 80 - 0.8 * (tempC - 25)
    humedadAirePct = round(min(100.0, max(0.0, humedad_base + random.uniform(-4.0, 4.0))), 1)

    # Battery slowly drains, stays mostly high
    bateriaPct = random.randint(70, 100)

    # WiFi RSSI: typical indoor range -90 to -30 dBm
    rssiDbm = round(random.uniform(-75.0, -45.0), 1)

    return {
        "tempC": tempC,
        "humedadAirePct": humedadAirePct,
        "bateriaPct": bateriaPct,
        "rssiDbm": rssiDbm,
    }


async def main():
    await client.connect()

    while not client.terminated():
        if client.is_connected():
            now = datetime.now(timezone.utc)
            payload = generate_reading(now)
            print(f"{now.isoformat()} -> {payload}")
            await client.send_telemetry(payload)
        await asyncio.sleep(25)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
