import os
import sys
import asyncio
import configparser
import importlib

from datetime import datetime, timedelta, timezone
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
    print("Usage: python sender_batch.py <device>")
    print("Available devices: estacion_clima, cultivo_cacao")
    sys.exit(1)

device = importlib.import_module(f"devices.{sys.argv[1]}")
prefix = device.ENV_PREFIX

device_id = os.environ[f"{prefix}_DEVICE_ID"]
scope_id = os.environ[f"{prefix}_SCOPE_ID"]
key = os.environ[f"{prefix}_DEVICE_KEY"]

DAYS_OF_HISTORY = 5
INTERVAL_MINUTES = 30


class MemStorage(Storage):
    def retrieve(self):
        return None

    def persist(self, credentials):
        return None


model_id = device.MODEL_ID

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

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=DAYS_OF_HISTORY)
    total_readings = DAYS_OF_HISTORY * 24 * (60 // INTERVAL_MINUTES)

    print(f"Sending {total_readings} readings from {start_time.isoformat()} to {now.isoformat()}")

    for i in range(total_readings):
        if client.is_connected():
            ts = start_time + timedelta(minutes=i * INTERVAL_MINUTES)
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")

            reading = device.generate_reading(ts)
            root = reading["telemetry"]
            root["$ts"] = ts_str

            try:
                await client.send_telemetry(root, {"iothub-creation-time-utc": ts_str})
                print(f"[{i+1}/{total_readings}] OK {ts_str} -> {root}")
            except Exception as e:
                print(f"[{i+1}/{total_readings}] FAILED {ts_str}: {e}")

            for comp_name, comp_data in reading["components"].items():
                comp_data["$ts"] = ts_str
                try:
                    await client.send_telemetry(comp_data, {"$.sub": comp_name, "iothub-creation-time-utc": ts_str})
                    print(f"  [{comp_name}] OK -> {comp_data}")
                except Exception as e:
                    print(f"  [{comp_name}] FAILED: {e}")

        await asyncio.sleep(0.3)

    print("Historical upload complete.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
