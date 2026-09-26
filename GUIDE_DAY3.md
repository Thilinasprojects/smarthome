# Day 3: Rooms and the Home

Today devices get somewhere to live. A `Room` holds devices, a `Home` holds rooms, and
one call, `home.all_off()`, reaches every device in the flat. This is **composition**:
building bigger objects out of smaller ones.

Today's work is in a new file, `src/smarthome/home.py` (a stub is in the zip).

## Setup (2 min)

```powershell
cd C:\code\projects\smarthome
Expand-Archive -Path $HOME\Downloads\smarthome-day3.zip -DestinationPath C:\code\projects -Force
uv run pytest -q
```

The zip adds `home.py` (a stub, since you don't have that file yet), the guide and the tests. **Extract it once only**, at the start of the day: extracting again would reset the stub file over your work.
Expect the 53 earlier tests to pass and today's to fail.

## The design

```
Home "My flat"
 └─ _rooms = { "Living room": Room, "Bedroom": Room }        a dict of Rooms
        Room "Living room"
         └─ _devices = { "ceiling": Light, "desk fan": Fan } a dict of Devices
```

**How the calls flow (always downhill):**

```
  home.all_off()
    └─► for each room:  room.all_off()
          └─► for each device:  device.turn_off()      (Light, Fan, Thermostat: any kind)

  home.power_draw
    └─► sum of room.power_draw
          └─► sum of device.power_draw                 (each kind does its own maths)

  home.find("Bedroom", "heater")
    └─► home["Bedroom"]     → Home.__getitem__  → the Room
          └─► room["heater"] → Room.__getitem__  → the Thermostat
```

Home never touches a device's settings, and a Room never knows which Home it's in.
Each layer only talks to the layer directly below it.

---

## Chunk 1: a Room (about 15 min)

Replace the stub `class Room: pass` in `home.py` with:

```python
class Room:
    """A named room holding devices, each with a unique name."""

    def __init__(self, name: str):
        self.name = name
        self._devices: dict[str, Device] = {}

    def add(self, device: Device) -> Device:
        if device.name in self._devices:
            raise DuplicateDevice(f"{self.name} already has a device called {device.name!r}")
        self._devices[device.name] = device
        return device  # so you can write: lamp = room.add(Light("lamp"))

    # ---- dunder methods: make a Room behave like a built-in container
    def __getitem__(self, name: str) -> Device:
        try:
            return self._devices[name]
        except KeyError:
            raise DeviceNotFound(f"no device {name!r} in {self.name}") from None

    def __contains__(self, name: str) -> bool:
        return name in self._devices

    def __len__(self) -> int:
        return len(self._devices)

    def __iter__(self):
        return iter(self._devices.values())

    def __repr__(self) -> str:
        return f"Room({self.name!r}, {len(self)} devices)"
```

**What the dunder methods buy you.** Each Python syntax calls one of them:

| You write | Python calls | Returns |
| --- | --- | --- |
| `room["ceiling"]` | `room.__getitem__("ceiling")` | the Light |
| `"ceiling" in room` | `room.__contains__("ceiling")` | `True` |
| `len(room)` | `room.__len__()` | `2` |
| `for d in room:` | `room.__iter__()` | each device in turn |
| `print(room)` | `room.__repr__()` | `Room('Living room', 2 devices)` |

The type hint `dict[str, Device]` says "a dict of names to Devices". Any kind of Device,
because a Room doesn't care whether it holds a light or a fan.

`from None` hides Python's internal `KeyError` and shows only your clear
`DeviceNotFound` message.

**Run:** `uv run pytest -q -k Chunk1` → 8 passed. **Commit.**

---

## Chunk 2: a Home (about 20 min)

**Step 1.** Add two things to `Room`, just above the `# ---- dunder methods` line:

```python
    def all_off(self) -> None:
        for device in self:
            device.turn_off()

    @property
    def power_draw(self) -> float:
        return sum(device.power_draw for device in self)
```

`for device in self` uses your own `__iter__`, so the Room uses its own dunder method.
And `device.turn_off()` is polymorphism: Room never asks what kind of device it has.

**Step 2.** A new error. Add to the bottom of `errors.py`:

```python
class DuplicateRoom(SmartHomeError):
    """Tried to add a second room with the same name to a home."""
```

and change the errors import at the top of `home.py` to:

```python
from smarthome.errors import DeviceNotFound, DuplicateDevice, DuplicateRoom
```

**Step 3.** Replace the stub `class Home: pass` with:

```python
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

    def __repr__(self) -> str:
        return f"Home({self.name!r}, {len(self._rooms)} rooms)"
```

Two new ideas:

- **`add_room` creates the Room itself** and hands it back. The Home owns its rooms, so it builds them. That's why you'll write `living = home.add_room("Living room")`.
- **`devices()` is a generator.** `yield` hands back one device at a time, pausing between them, and `yield from room` means "yield everything the room yields". So `for d in home.devices():` walks the whole flat without ever building a big list.

**Run:** `uv run pytest -q -k Chunk2` → 9 passed. **Commit.**

**Try it** (`uv run python`):

```python
from smarthome.home import Home
from smarthome import Light, Fan
home = Home("My flat")
living = home.add_room("Living room")
living.add(Light("ceiling")).turn_on()   # add returns the light, so you can switch it at once
living.add(Fan("desk fan"))
home.power_draw
gen = home.devices()
next(gen)          # the ceiling light
next(gen)          # the fan
next(gen)          # StopIteration: nothing left
```

---

## Chunk 3: the report and your own flat (about 15 min)

**Step 1.** Add to `Home`, just above `__repr__`:

```python
    # ---- the text report
    def report(self) -> str:
        lines = [f"{self.name} — total draw {self.power_draw:,.1f} W"]
        for room in self._rooms.values():
            lines.append(f"  {room.name}")
            for d in room:
                state = "ON" if d.is_on else "OFF"
                lines.append(
                    f"    {d.name:<12} {type(d).__name__:<11} {state:<4} "
                    f"{d.status():<10} {d.power_draw:>7.1f} W"
                )
        return "\n".join(lines)
```

`:<12` pads to 12 characters, aligned left; `:>7.1f` means 7 wide, aligned right, 1 decimal
place; `:,` adds thousands commas. That's how the columns line up.

(The — is an em dash. If it's hard to type, copy it from here. The test checks for it.)

**Step 2.** Replace `src/smarthome/__init__.py` with:

```python
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
    "DuplicateRoom",
    "Fan",
    "Home",
    "InvalidSetting",
    "Light",
    "Room",
    "SmartHomeError",
    "Thermostat",
]
```

**Step 3.** Replace `examples/my_flat.py` with your real home. Change the rooms and devices
to match where you live:

```python
"""My flat, built in code.   uv run python examples/my_flat.py"""

from smarthome import Fan, Home, Light, Thermostat

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
```

**Run:** `uv run pytest -q -k Chunk3` → 1 passed, then `uv run python examples/my_flat.py`. **Commit.**

---

## Your turn: `remove()` and `find()`

1. **`Room.remove(name)`** takes a device out of the room and **returns** it. If there's
   no device with that name, raise `DeviceNotFound`. (Tip: `dict.pop(key)` removes and returns in one step.)
2. **`Home.find(room, device)`** returns the device, e.g. `home.find("Bedroom", "heater")`.
   If either the room or the device is missing, `DeviceNotFound`. This one is a single line if
   you reuse what you've already built.

**Run:** `uv run pytest -q -k YourTurn` → 4 passed. Then `uv run pytest -q` → **75 passed**.

<details><summary>Hint for find()</summary>

`self[room]` gives you the Room (your `Home.__getitem__`), and `room_object[device]`
gives you the device (your `Room.__getitem__`). Chain them: `return self[room][device]`.
Both already raise `DeviceNotFound`, so you get the errors for free.

</details>

**Commit and push.**

## What to remember from today

1. **Composition**: big objects hold smaller ones (Home → Room → Device), usually in a dict or list.
2. **Delegate downhill**: each layer asks the layer below; nothing reaches up.
3. **Dunder methods** make your objects work with `[]`, `in`, `len()` and `for`.
4. **Generators** (`yield`) walk through things one at a time.
5. **Reuse** your own methods: `find` is one line because `[]` already works.
