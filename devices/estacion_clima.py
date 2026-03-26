import random
import math

ENV_PREFIX = "CLIMA"
MODEL_ID = None


def generate_reading(ts):
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
        "telemetry": {
            "tempExternaC": tempExternaC,
            "humedadExternaPct": humedadExternaPct,
            "vientoMps": vientoMps,
            "lluviaMm": lluviaMm,
        },
        "components": {},
    }
