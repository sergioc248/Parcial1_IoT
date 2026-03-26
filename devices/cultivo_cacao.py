import random
import math

ENV_PREFIX = "CACAO"
MODEL_ID = "dtmi:unab:greenhouse:NodoCultivoBase;1"


def generate_reading(ts):
    # Cacao optimal range: 18-32°C, mild daily cycle
    hour = ts.hour + ts.minute / 60.0
    temp_base = 25 + 4 * math.sin(math.pi * (hour - 6) / 12)  # peaks ~18:00
    tempC = round(temp_base + random.uniform(-1.5, 1.5), 1)

    # High humidity environment (70-90%), inversely correlated with temperature
    humedad_base = 80 - 0.8 * (tempC - 25)
    humedadAirePct = round(min(100.0, max(0.0, humedad_base + random.uniform(-4.0, 4.0))), 1)

    # Battery slowly drains, stays mostly high
    bateriaPct = random.randint(70, 100)

    # WiFi RSSI: typical indoor range -90 to -30 dBm
    rssiDbm = round(random.uniform(-75.0, -45.0), 1)

    # Soil moisture: cacao prefers moist substrate (50-80%)
    humedadSueloPct = round(random.uniform(50.0, 80.0), 0)

    # Substrate pH: cacao optimal range 5.5-7.0
    ph = round(random.uniform(5.5, 7.0), 2)

    # CO2: greenhouse levels, higher during day due to plant activity
    co2_base = 800 + 300 * math.sin(math.pi * (hour - 6) / 12)  # peaks midday
    co2ppm = round(max(400.0, co2_base + random.uniform(-50.0, 50.0)), 0)

    # Illuminance: filtered greenhouse light, peaks at midday (0 at night)
    if 6 <= hour <= 18:
        lux_base = 20000 * math.sin(math.pi * (hour - 6) / 12)
        luminosidadLux = round(max(0.0, lux_base + random.uniform(-1000.0, 1000.0)), 0)
    else:
        luminosidadLux = 0.0

    return {
        "telemetry": {
            "tempC": tempC,
            "humedadAirePct": humedadAirePct,
            "bateriaPct": bateriaPct,
            "rssiDbm": rssiDbm,
        },
        "components": {
            "NodoCultivoBase_60o": {"humedadSueloPct": humedadSueloPct},
            "NodoCultivoBase_2jw": {"ph": ph},
            "NodoCultivoBase_6mr": {"co2ppm": co2ppm},
            "NodoCultivoBase_2xc": {"luminosidadLux": luminosidadLux},
        },
    }
