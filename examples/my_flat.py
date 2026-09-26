"""Your home, built in code. It grows every day.

Run:  uv run python examples/my_flat.py
"""

from smarthome import Light, Fan, Home, Thermostat

home = Home("My flat")

living = home.add_room("Living room")
living.add(Light("ceiling", watts=12))
living.add(Light("desk lamp", watts=8))
living.add(Fan("desk fan", watts=40))

bedroom = home.add_room("Bedroom")
bedroom.add(Light("bedside", watts=6))
bedroom.add(Thermostat("heater", watts=1500, target=19))

living["ceiling"].turn_on()
living["ceiling"].brightness = 60
bedroom["heater"].turn_on()

print(home.report())
print()
home.all_off()
print(home.report())
