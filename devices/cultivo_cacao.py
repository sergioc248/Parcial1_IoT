import random
import math

ENV_PREFIX = "CACAO"


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

    return {
        "tempC": tempC,
        "humedadAirePct": humedadAirePct,
        "bateriaPct": bateriaPct,
        "rssiDbm": rssiDbm,
    }
