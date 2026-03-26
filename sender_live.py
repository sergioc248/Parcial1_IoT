import os
import sys
import asyncio
import configparser
import importlib

from datetime import datetime, timezone
from dotenv import load_dotenv
from iotc.models import Property, Command

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "samples.ini"))
if config["DEFAULT"].getboolean("Local"):
    sys.path.insert(0, "src")

from iotc import IOTCConnectType, IOTCLogLevel, IOTCEvents, Command, CredentialsCache, Storage
from iotc.aio import IoTCClient

if len(sys.argv) < 2:
    print("Usage: python sender_live.py <device>")
    print("Available devices: estacion_clima, cultivo_cacao")
    sys.exit(1)

device = importlib.import_module(f"devices.{sys.argv[1]}")
prefix = device.ENV_PREFIX

device_id = os.environ[f"{prefix}_DEVICE_ID"]
scope_id = os.environ[f"{prefix}_SCOPE_ID"]
key = os.environ[f"{prefix}_DEVICE_KEY"]


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


async def main():
    await client.connect()

    while not client.terminated():
        if client.is_connected():
            now = datetime.now(timezone.utc)
            payload = device.generate_reading(now)
            print(f"{now.isoformat()} -> {payload}")
            await client.send_telemetry(payload)
        await asyncio.sleep(25)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
