"""Rooms and the Home: containers that hold devices."""

from smarthome.devices import Device
from smarthome.errors import DeviceNotFound, DuplicateDevice


class Room:
    """A named room holding devices, each with a unique name."""

    def __init__(self, name: str):
        self.name = name
        self._devices: dict[str, Device] = {}

    def add(self, device: Device) -> Device:
        if device.name in self._devices:
            raise DuplicateDevice(f"{self.name} already has a device called {device.name!r}")
        self._devices[device.name] = device
        return device  # So you can write: lamp = room.add(Light("lamp"))

    # ---- dunder methods: make a Room behave like a built-in container.
    def __getitem__(self, name: str) -> Device:
        try:
            return self._devices[name]
        except KeyError:
            raise DeviceNotFound(f"no device {name!r} in {self.name}") from None

    def __contains__(self, name: str) -> bool:
        return name in self._devices  # return True or False, if the given device is in the room.

    def __len__(self) -> int:
        return len(self._devices)

    def __iter__(self):
        return iter(self._devices.values())

    def __repr__(self) -> str:
        return f"Room({self.name!r}, {len(self)} devices)"


class Home:
    pass  # Chunk 2: replace this class, see GUIDE_DAY3.md
