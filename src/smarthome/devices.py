"""Devices in the home. Day 1: a Light, on its own.

Type the Light class from GUIDE_DAY1.md over the stub below, one chunk at a time.
"""

from smarthome.errors import InvalidSetting


class Light:
    """A dimmable light."""

    def __init__(self, name: str, watts: float = 10.0):
        # __init__ runs once, when you write Light("ceiling").
        # It's job: set the new object up in a valid starting state, or refuse to create it at all.
        if watts <= 0:
            raise InvalidSetting(f"watts must be > 0, got {watts!r}")

        self.name = name  # public: anyone may read or rename it
        self.watts = watts  # the rated power on the box

        # Leading underscore = private: only the Light's own methods change these.
        self._is_on = False
        self._brightness = 100  # percent
        self._energy_kwh = 0.0  # the meter

    @property
    def is_on(self) -> bool:
        # A property with no setter: 'Light.is_on' reads it, 'light.is_on = True' is refused. The only
        # way to switch is through the methods below.
        return self._is_on

    def turn_on(self) -> None:
        self._is_on = True

    def turn_off(self) -> None:
        self._is_on = False

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        # The setter runs when someone writes 'Light.brightness = 40'.
        # Check first, change after: a refused value leaves the light untouched.
        if not 0 <= value <= 100:
            raise InvalidSetting(f"brightness must be 0-100%, got {value!r}")
        self._brightness = value

    @property
    def power_draw(self) -> float:
        """Watts being used right now"""
        # worked out fresh every time it's read, so it can be out of date.
        if not self._is_on:
            return 0.0
        return self.watts * self._brightness / 100

    @property
    def energy_kwh(self) -> float:
        """Total energy used so far, in kilowatt-hours (what the bill counts)."""
        return self._energy_kwh

    def run(self, hours: float) -> None:
        """Let time pass: add this period's energy to the meter."""
        if hours < 0:
            raise InvalidSetting(f"hours can't be negative, got{hours!r}")
        # watts x hours = watt-hours; divide by 1000 for kilowatt-hours
        self._energy_kwh += self.power_draw * hours / 1000

    def __repr__(self) -> str:
        # what Python shows when you print the object or look at it in the REPL.
        state = "on" if self._is_on else "off"
        return f"Light({self.name!r}, {state}, {self._brightness}%)"
