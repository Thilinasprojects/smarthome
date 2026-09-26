"""Rooms and the Home: containers that hold devices."""

from smarthome.devices import Device
from smarthome.errors import DeviceNotFound, DuplicateDevice, DuplicateRoom


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

    def remove(self, name) -> Device:
        if name not in self._devices:
            raise DeviceNotFound(f"no device {name!r} in {self.name}.")
        return self._devices.pop(name)

    def all_off(self) -> None:
        for device in self:
            device.turn_off()

    @property
    def power_draw(self) -> float:
        return sum(device.power_draw for device in self)

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
    """The whole home: rooms, and everything in them."""

    def __init__(self, name: str):
        self.name = name
        self._rooms: dict[str, Room] = {}

    # ---- rooms
    def add_room(self, name: str) -> Room:
        if name in self._rooms:
            raise DuplicateRoom(f"{self.name} already has a room called {name!r}")
        room = Room(name)
        self._rooms[name] = room
        return room

    @property
    def rooms(self) -> tuple[Room, ...]:
        return tuple(self._rooms.values())

    def find(self, room_name: str, device_name: str):
        return self.__getitem__(room_name).__getitem__(device_name)

    def __getitem__(self, name: str) -> Room:
        try:
            return self._rooms[name]
        except KeyError:
            raise DeviceNotFound(f"no room called {name!r}") from None

    # ---- all devices, everywhere
    def devices(self):
        """Yield every device in every room, one at a time."""
        for room in self._rooms.values():
            yield from room

    def all_off(self) -> None:
        for room in self._rooms.values():
            room.all_off()

    @property
    def power_draw(self) -> float:
        return sum(room.power_draw for room in self._rooms.values())

    # ---- the text report
    def report(self) -> str:
        lines = [f"{self.name} - total draw {self.power_draw:,.1f} W"]
        for room in self._rooms.values():
            lines.append(f"  {room.name}")
            for d in room:
                state = "ON" if d.is_on else "OFF"
                lines.append(
                    f"    {d.name < 12} {type(d).__name__:<11} {state:<4} "
                    f"{d.status():<10} {d.power_draw:>7.1f} W"
                )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Home({self.name!r}, {len(self._rooms)} rooms)"
