# Day 4: time, saving, and scenes

Today the home comes alive. Time passes and the meter runs up a bill, the whole flat
saves to a file and loads back, and scenes change several devices in one go. Then you
write a new kind of device, `SmartPlug`, completely on your own.

It's a long day with four chunks. Take a proper break after Chunk 2.

## Setup (2 min)

```powershell
cd C:\code\projects\smarthome
Expand-Archive -Path $HOME\Downloads\smarthome-day4.zip -DestinationPath C:\code\projects -Force
uv run pytest -q
```

The zip adds a stub `scenes.py` (a new file), the guide and the tests. The 75 earlier tests should pass. **Extract it once only**, at the start of the day: extracting again would reset the stub file over your work.

---

## Chunk 1: time passes, the bill arrives (about 10 min)

```
  home.run(hours=2)
    └─► for device in home.devices():      (your Day 3 generator)
          device.run(2)                     (Day 1: adds power_draw x hours to its own meter)

  home.bill(0.25)
    └─► home.energy_kwh  = sum of every device.energy_kwh
          └─► x price, rounded to pennies
```

Add to `Home` in `home.py`, just above `# ---- the text report`:

```python
    # ---- time, energy and money
    def run(self, hours: float) -> None:
        for device in self.devices():
            device.run(hours)

    @property
    def energy_kwh(self) -> float:
        return sum(device.energy_kwh for device in self.devices())

    def bill(self, price_per_kwh: float) -> float:
        return round(self.energy_kwh * price_per_kwh, 2)
```

Each device keeps its **own** meter. Home only asks and adds up. It's the same shape as
`power_draw` on Day 3.

**Run:** `uv run pytest -q -k Chunk1` → 3 passed. **Commit.**

---

## Chunk 2: a device becomes data, and data becomes a device (about 25 min)

To save a home to a file, every object must turn itself into plain data (dicts, lists,
text, numbers), and later be rebuilt from that data.

```
  SAVING                                       LOADING
  light.to_dict()                              Device.from_dict(data)
    └─► {"kind": "light",       ◄── kind         └─► DEVICE_TYPES["light"]  →  Light
         "name": "ceiling",                       └─► Light("ceiling", watts=12)
         "watts": 12,                             └─► for each setting:
         "is_on": true,                                 setattr(light, "brightness", 40)
         "settings": {"brightness": 40}}                  └─► goes through your setter, so it's checked!
              ▲                                    └─► turn_on() if it was on
              └── light.settings()  (each kind knows its own)
```

**Step 1.** Every kind of device must describe its own settings. Add this abstract method
to `Device`, just below the abstract `status`:

```python
    @abstractmethod
    def settings(self) -> dict:
        """The device's own settings as a dict, for saving, e.g. {'brightness': 40}."""
```

Try `uv run pytest -q` now: every device test fails with "Can't instantiate abstract
class". That's the contract working: a child that doesn't provide `settings()` can't
be created. Fix it by adding a `settings()` method to **each** child class, next to its `status()`:

```python
    def settings(self) -> dict:          # in Light
        return {"brightness": self._brightness}
```

```python
    def settings(self) -> dict:          # in Fan
        return {"speed": self._speed}
```

```python
    def settings(self) -> dict:          # in Thermostat
        return {"target": self._target}
```

**Step 2.** Add saving and loading to `Device`, just above its `__repr__`:

```python
    # ---- saving and loading
    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "name": self.name,
            "watts": self.watts,
            "is_on": self._is_on,
            "settings": self.settings(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        device_class = DEVICE_TYPES[data["kind"]]
        device = device_class(data["name"], watts=data["watts"])
        for setting, value in data["settings"].items():
            setattr(device, setting, value)
        if data["is_on"]:
            device.turn_on()
        return device
```

**Step 3.** At the very **bottom** of `devices.py`, after all the classes, add the registry:

```python
# Registry: turns the "kind" text in a saved file back into a class.
DEVICE_TYPES: dict[str, type[Device]] = {
    "light": Light,
    "fan": Fan,
    "thermostat": Thermostat,
}
```

Three new ideas:

- **`@classmethod`** gets the class (`cls`) instead of an object (`self`). It's a second
  way to make objects: `Device.from_dict(data)` instead of `Light(...)`. People call this a
  **factory**: you hand it data, and it decides which class to build.
- **The registry** is a plain dict from text to classes. Classes are objects in Python,
  so you can store them in a dict and call them later: `DEVICE_TYPES["fan"]("desk fan")` builds a Fan.
  That's how the word "fan" in a file becomes a real `Fan`.
- **`setattr(device, "brightness", 40)`** is the same as `device.brightness = 40`, but
  with the name as text. It still goes through your setter, so a file saying brightness 500
  is refused. Loading can't sneak past validation.

**Run:** `uv run pytest -q -k Chunk2` → 5 passed. **Commit.**

**Try it** (`uv run python`):

```python
from smarthome.devices import Device, Fan
f = Fan("desk fan"); f.speed = 3; f.turn_on()
data = f.to_dict(); data
copy = Device.from_dict(data); copy       # a new Fan, same state
copy is f                                 # False: a separate object
```

---

## Chunk 3: save and load the whole home (about 15 min)

Rooms and the Home do the same thing, each asking the layer below:

```
  home.save("home.json")
    └─► home.to_dict()  →  {"name": ..., "rooms": [room.to_dict(), ...]}
          room.to_dict() →  {"name": ..., "devices": [device.to_dict(), ...]}
    └─► json.dumps(...) → text → written to the file

  Home.load("home.json")
    └─► read the file → json.loads → dict
    └─► Home.from_dict(dict)
          └─► Home(name) → add_room(...) → room.add(Device.from_dict(...))
```

**Step 1.** Add to `Room`, just above `# ---- dunder methods`:

```python
    def to_dict(self) -> dict:
        return {"name": self.name, "devices": [device.to_dict() for device in self]}
```

**Step 2.** At the top of `home.py`, add these two imports above the others:

```python
import json
from pathlib import Path
```

**Step 3.** Add to `Home`, just above its `__repr__`:

```python
    # ---- saving and loading
    def to_dict(self) -> dict:
        return {"name": self.name, "rooms": [room.to_dict() for room in self._rooms.values()]}

    @classmethod
    def from_dict(cls, data: dict) -> "Home":
        home = cls(data["name"])
        for room_data in data["rooms"]:
            room = home.add_room(room_data["name"])
            for device_data in room_data["devices"]:
                room.add(Device.from_dict(device_data))
        return home

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Home":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
```

Notice `from_dict` doesn't bypass anything. It rebuilds the home with your normal
`add_room` and `add`, so every rule (no duplicate names, valid settings) still applies.

**Run:** `uv run pytest -q -k Chunk3` → 3 passed. **Commit.**

**Try it:** add these lines to the end of `examples/my_flat.py`, run it, then open `home.json` in VS Code:

```python
home.save("home.json")
again = Home.load("home.json")
print(again.report() == home.report())   # True: a perfect round trip
```

Add `home.json` to `.gitignore`: it's your data, not code.

---

## Chunk 4: scenes (about 20 min)

A scene is a saved list of changes, like "Movie night: ceiling at 20 %, fan on, heater off".
Scenes are **just data**, so they're dataclasses.

```
  home.apply(movie)
    └─► 1. CHECK: find every device first     (a typo raises DeviceNotFound, nothing changed)
    └─► 2. CHANGE: for each action:
            "on"         → device.turn_on()
            "off"        → device.turn_off()
            "brightness" → setattr(...)  → your setter checks the value
```

**Step 1.** Replace everything in `scenes.py` with:

```python
"""Scenes: saved sets of changes, like "Movie night"."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Action:
    """One change: e.g. room 'Living room', device 'ceiling', setting 'brightness', value 20.

    setting is "on", "off", or the name of a device property ("brightness", "speed", "target").
    """

    room: str
    device: str
    setting: str
    value: object = None


@dataclass
class Scene:
    """A named list of Actions."""

    name: str
    actions: list[Action] = field(default_factory=list)

    def add(self, room: str, device: str, setting: str, value: object = None) -> "Scene":
        self.actions.append(Action(room, device, setting, value))
        return self  # returning self lets you chain: scene.add(...).add(...)

    def __len__(self) -> int:
        return len(self.actions)
```

- **`Action` is frozen**, because a single change is a fact that shouldn't be edited.
  **`Scene` isn't frozen**, because you add actions to it.
- **`field(default_factory=list)`** gives every Scene its **own** new list. Writing `= []` would
  make all scenes share one list: a classic Python trap, and dataclasses refuse to let you do it.
- **`return self`** allows chaining: `Scene("x").add(...).add(...)`.

**Step 2.** In `home.py`, update the errors import and import `Scene`:

```python
from smarthome.errors import DeviceNotFound, DuplicateDevice, DuplicateRoom, InvalidSetting
from smarthome.scenes import Scene
```

**Step 3.** Add to `Home`, just above `# ---- the text report`:

```python
    # ---- scenes
    def apply(self, scene: Scene) -> None:
        # Check first: find every device before changing anything,
        # so a typo in the last action doesn't leave the scene half-applied.
        targets = [(self.find(a.room, a.device), a) for a in scene.actions]
        for device, action in targets:
            if action.setting == "on":
                device.turn_on()
            elif action.setting == "off":
                device.turn_off()
            elif action.setting in device.settings():
                setattr(device, action.setting, action.value)
            else:
                raise InvalidSetting(f"{device.name} has no setting {action.setting!r}")
```

The first line is "check first, change after" applied to a whole list: if any device name
is wrong, nothing changes at all. (A bad *value*, like brightness 500, is still only caught
when its turn comes. Checking values up front too would make a good extension later.)

**Run:** `uv run pytest -q -k Chunk4` → 5 passed. **Commit.**

---

## Your turn: `SmartPlug`, completely on your own

A smart plug switches whatever is plugged into it: a kettle, a lamp, a charger.
Write `class SmartPlug(Device)` in `devices.py`. The spec:

| | |
| --- | --- |
| `kind` | `"plug"` |
| Constructor | `SmartPlug(name, watts=10.0)`, the same as `Device`. Do you even need to write an `__init__`? |
| `power_draw` | full `watts` when on, `0.0` when off |
| `status()` | `"-"` (a plug has no setting) |
| `settings()` | `{}` |
| Registry | add it to `DEVICE_TYPES`, so it can be saved and loaded |

Then add `SmartPlug` to `__init__.py` (the import line and `__all__`).

**Run:** `uv run pytest -q -k YourTurn` → 5 passed, then `uv run pytest -q` → **96 passed**.

<details><summary>Hint: the __init__ question</summary>

No. If a child doesn't define `__init__`, Python uses the parent's. SmartPlug has no
extra settings, so `Device.__init__` already does everything it needs.

</details>

**Last bit, just for fun (no test):** in `examples/my_flat.py`, plug a kettle into the
kitchen, write a "night" scene that turns everything off and sets the heater to 17, apply
it, run 8 hours, and print the bill.

**Commit and push.** That's the whole model finished. Tomorrow you give it a face.

## What to remember from today

1. **Each object keeps its own data** (its meter, its settings); containers ask and add up.
2. **`to_dict` / `from_dict`** turn objects into plain data and back, layer by layer.
3. **`@classmethod`** gives a second way to build objects: a factory.
4. **A registry** (a dict of classes) turns text into the right class.
5. **Dataclasses** are for pure data; `default_factory=list` avoids the shared-list trap.
6. **Validation survives loading**, because `setattr` goes through your setters.
