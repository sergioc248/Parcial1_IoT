import os
import sys
import asyncio
import configparser
import importlib
import threading

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

DISCONNECTED_TIMEOUT = 120  # seconds before giving up and reconnecting

# Event loop reference and restart flag, set once the loop is running
_loop = None
_restart_event = None


def thread_exception_handler(args):
    print(f"Background thread error: {args.exc_value}. Triggering restart...")
    if _loop is not None and _restart_event is not None:
        _loop.call_soon_threadsafe(_restart_event.set)


threading.excepthook = thread_exception_handler


class MemStorage(Storage):
    def retrieve(self):
        return None

    def persist(self, credentials):
        return None


async def on_props(prop: Property):
    print(f"Received {prop.name}:{prop.value}")
    return True

async def on_commands(command: Command):
    print("Received command {} with value {}".format(command.name, command.value))
    await command.reply()

async def on_enqueued_commands(command: Command):
    print("Received offline command {} with value {}".format(command.name, command.value))


def make_client():
    client = IoTCClient(
        device_id,
        scope_id,
        IOTCConnectType.IOTC_CONNECT_DEVICE_KEY,
        key,
        storage=MemStorage(),
    )
    if device.MODEL_ID is not None:
        client.set_model_id(device.MODEL_ID)
    client.set_log_level(IOTCLogLevel.IOTC_LOGGING_ALL)
    client.on(IOTCEvents.IOTC_PROPERTIES, on_props)
    client.on(IOTCEvents.IOTC_COMMAND, on_commands)
    client.on(IOTCEvents.IOTC_ENQUEUED_COMMAND, on_enqueued_commands)
    return client


async def run():
    global _restart_event
    _restart_event = asyncio.Event()

    client = make_client()
    await client.connect()

    disconnected_since = None

    while not client.terminated():
        if _restart_event.is_set():
            raise ConnectionError("Connection dropped in background thread, restarting...")

        if client.is_connected():
            disconnected_since = None
            now = datetime.now(timezone.utc)
            reading = device.generate_reading(now)

            await client.send_telemetry(reading["telemetry"])
            print(f"{now.isoformat()} -> {reading['telemetry']}")

            for comp_name, comp_data in reading["components"].items():
                await client.send_telemetry(comp_data, {"$.sub": comp_name})
                print(f"  [{comp_name}] -> {comp_data}")

        else:
            if disconnected_since is None:
                disconnected_since = datetime.now(timezone.utc)
                print("Disconnected from Azure, waiting to reconnect...")
            elif (datetime.now(timezone.utc) - disconnected_since).total_seconds() > DISCONNECTED_TIMEOUT:
                raise ConnectionError(f"Disconnected for over {DISCONNECTED_TIMEOUT}s, restarting...")

        await asyncio.sleep(25)

    await client.disconnect()


async def main():
    global _loop
    _loop = asyncio.get_running_loop()

    retry_delay = 5
    while True:
        try:
            await run()
        except KeyboardInterrupt:
            print("Shutting down.")
            break
        except BaseException as e:
            print(f"Connection error: {e}. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)


if __name__ == "__main__":
    asyncio.run(main())
