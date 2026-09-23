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
