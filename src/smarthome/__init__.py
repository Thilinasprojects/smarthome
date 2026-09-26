"""smarthome: a simulated smart home for learning OOP."""

from smarthome.devices import Device, Fan, Light, Thermostat
from smarthome.errors import (
    DeviceNotFound,
    DuplicateDevice,
    DuplicateRoom,
    InvalidSetting,
    SmartHomeError,
)
from smarthome.home import Home, Room

__all__ = [
    "Device",
    "DeviceNotFound",
    "DuplicateDevice",
    "Room",
    "DuplicateRoom",
    "Fan",
    "Home",
    "Room",
    "InvalidSetting",
    "Light",
    "SmartHomeError",
    "Thermostat",
]
