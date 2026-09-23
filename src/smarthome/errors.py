"""Errors with names that say what went wrong.

All of them inherit from SmartHomeError, so `except SmartHomeError` catches any of them.
"""


class SmartHomeError(Exception):
    """Base class for every smart-home problem."""


class InvalidSetting(SmartHomeError):
    """A value outside what the device allows, e.g. brightness 150."""


class DeviceNotFound(SmartHomeError):
    """Asked for a device or room that doesn't exist."""


class DuplicateDevice(SmartHomeError):
    """Tried to add a second device with the same name to a room."""
