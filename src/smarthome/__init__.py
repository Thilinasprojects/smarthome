"""smarthome: a simulated smart home for learning OOP."""

from smarthome.devices import Device, Fan, Light
from smarthome.errors import DeviceNotFound, DuplicateDevice, InvalidSetting, SmartHomeError

__all__ = [
    "Device",
    "DeviceNotFound",
    "DuplicateDevice",
    "Fan",
    "InvalidSetting",
    "Light",
    "SmartHomeError",
]
