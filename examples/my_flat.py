"""Your home, built in code. It grows every day.

Run:  uv run python examples/my_flat.py
"""

from smarthome import InvalidSetting, Light

ceiling = Light("ceiling", watts=12)
print(ceiling)

ceiling.turn_on()
ceiling.brightness = 40
print(ceiling, "draws", ceiling.power_draw, "W")

try:
    ceiling.brightness = 150
except InvalidSetting as err:
    print("Refused:", err)

ceiling.run(hours=3)
print(f"Energy used: {ceiling.energy_kwh:.4f} kWh")
