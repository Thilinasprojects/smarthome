"""Devices in the home. Day 1: a Light, on its own.

Type the Light class from GUIDE_DAY1.md over the stub below, one chunk at a time.
"""

from abc import ABC, abstractmethod
from smarthome.errors import InvalidSetting


class Device(ABC):
    """Anything in the home that can be switched on and draws power.

    Abstract: you can't create a plain Device, only a kind of device.
    """

    def __init__(self, name: str, watts: float = 10.0):
        if watts <= 0:
            raise InvalidSetting(f"watts must be > 0, got {watts!r}")
        self.name = name
        self.watts = watts
        self._is_on = False
        self._energy_kwh = 0.0

    # ---- switching: shhared by every device
    @property
    def is_on(self) -> bool:
        return self._is_on

    def turn_on(self) -> None:
        self._is_on = True

    def turn_off(self) -> None:
        self._is_on = False

    def toggle(self) -> None:
        if self._is_on:
            self.turn_off()
        else:
            self.turn_on()

    # ---- energy: shared by every device
    @property
    def energy_kwh(self) -> float:
        return self._energy_kwh

    def run(self, hours: float) -> None:
        if hours < 0:
            raise InvalidSetting(f"hours can't be negative, got {hours!r}")
        self._energy_kwh += self.power_draw * hours / 1000

    # ---- what each kind of device must provide for itself
    @property
    @abstractmethod
    def power_draw(self) -> float:
        """Watts being used right now"""

    def status(self) -> str:
        """The devices own setting, short, e.g. '40%' or 'speed 2'."""

    def __repr__(self) -> str:
        state = "on" if self._is_on else "off"
        return f"{type(self).__name__}({self.name!r}, {state}, {self.status()})"


class Light(Device):
    """A dimmable light."""

    def __init__(self, name: str, watts: float = 10.0):
        super().__init__(name, watts)
        self._brightness = 100

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

    def status(self) -> str:
        return f"{self._brightness}%"


class Fan(Device):
    """A fan with speed 1 to 3."""

    MAX_SPEED = 3  # a class attribute: the same for every fan.

    def __init__(self, name: str, watts: float = 40.0):
        super().__init__(name, watts)
        self._speed = 1

    @property
    def speed(self) -> int:
        return self._speed

    @speed.setter
    def speed(self, value: int) -> None:
        if value not in range(1, self.MAX_SPEED + 1):
            raise InvalidSetting(f"speed must be 1-{self.MAX_SPEED}, got {value!r}")
        self._speed = value

    @property
    def power_draw(self) -> float:
        if not self._is_on:
            return 0.0
        return self.watts * self._speed / self.MAX_SPEED

    def status(self) -> str:
        return f"speed {self._speed}"
