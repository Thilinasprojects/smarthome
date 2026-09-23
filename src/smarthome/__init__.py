"""smarthome: a simulated smart home for learning OOP."""

from smarthome.devices import Light
from smarthome.errors import DeviceNotFound, DuplicateDevice, InvalidSetting, SmartHomeError

__all__ = ["DeviceNotFound", "DuplicateDevice", "InvalidSetting", "Light", "SmartHomeError"]
