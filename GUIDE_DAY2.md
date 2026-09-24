# Day 2: the Device family

Today you add a `Fan`, notice how much of it is copied from `Light`, and fix that
with a parent class, `Device`. Then you write `Thermostat` mostly by yourself.

All of today happens in `src/smarthome/devices.py`.

## Setup (2 min)

```powershell
cd C:\code\projects\smarthome
Expand-Archive -Path $HOME\Downloads\smarthome-day2.zip -DestinationPath C:\code\projects -Force
uv run pytest -q
```

`-Force` lets the zip add today's guide and tests into your existing project. It
contains no `src` files, so your code is never overwritten. Expect Day 1's 24 tests to
pass and today's to fail.

---

## Chunk 1: a Fan, the copy-and-paste way (about 15 min)

A fan is like a light, but instead of a dimmer it has speeds 1, 2 and 3.
Add this class at the **bottom** of `devices.py`, below `Light`:

```python
class Fan:
    """A fan with speeds 1 to 3."""

    MAX_SPEED = 3  # a class attribute: the same for every fan

    def __init__(self, name: str, watts: float = 40.0):
        if watts <= 0:
            raise InvalidSetting(f"watts must be > 0, got {watts!r}")
        self.name = name
        self.watts = watts
        self._is_on = False
        self._speed = 1
        self._energy_kwh = 0.0

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

    @property
    def energy_kwh(self) -> float:
        return self._energy_kwh

    def run(self, hours: float) -> None:
        if hours < 0:
            raise InvalidSetting(f"hours can't be negative, got {hours!r}")
        self._energy_kwh += self.power_draw * hours / 1000

    def __repr__(self) -> str:
        state = "on" if self._is_on else "off"
        return f"Fan({self.name!r}, {state}, speed {self._speed})"
```

**Run:** `uv run pytest -q -k Chunk1` → 16 passed (6 from Day 1, 10 for the fan). **Commit.**

**Now look at it next to `Light`.** Put the two classes side by side
(right-click the `devices.py` tab → **Split Right**). Count the lines that are the same:

```
                         Light   Fan
  watts check in __init__   ✓      ✓     identical
  name, watts, _is_on,      ✓      ✓     identical
  _energy_kwh
  is_on                     ✓      ✓     identical
  turn_on / turn_off        ✓      ✓     identical
  toggle                    ✓      ✓     identical
  energy_kwh, run           ✓      ✓     identical
  __repr__                  ✓      ✓     same shape, different last part
  brightness / speed        own    own   DIFFERENT
  power_draw                own    own   DIFFERENT maths
```

About 30 lines are copies. A thermostat would copy them again, then a plug, then a kettle.
And if you found a bug in `run()`, you'd have to fix it in every copy. That's the
problem inheritance solves.

---

## Chunk 2: pull the shared code up into `Device` (about 20 min)

The idea: put everything the devices **share** in one parent class. Each child keeps
only what makes it **different**.

```
        Device (abstract)                        Light(Device)
  ┌───────────────────────────────┐        ┌───────────────────────────────┐
  │ __init__: name, watts,         │ ◄───── │ __init__: super().__init__()   │
  │           _is_on, _energy_kwh  │ super  │           + _brightness        │
  │ is_on, turn_on, turn_off,      │        │ brightness (setter checks)     │
  │ toggle                         │        │                                │
  │ energy_kwh                     │        │                                │
  │ run(hours) ── self.power_draw ─┼──────► │ power_draw  (its own maths)    │
  │ __repr__  ─── self.status() ───┼──────► │ status()    "40%"              │
  │                                │        │                                │
  │ power_draw   abstract, no body │        └───────────────────────────────┘
  │ status()     abstract, no body │        Fan(Device): same shape, with speed
  └───────────────────────────────┘
```

The arrows on the right are the important bit: **Device's own methods call methods
that only the child defines.** `run()` is written once, but `self` is a real Light or Fan,
so `self.power_draw` runs the child's version. That's polymorphism.

**Step 1.** Add this import at the top of `devices.py`, above the existing import:

```python
from abc import ABC, abstractmethod
```

**Step 2.** Add `Device` **above** `Light`:

```python
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

    # ---- switching: shared by every device
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
        """Watts being used right now."""

    @abstractmethod
    def status(self) -> str:
        """The device's own setting, short, e.g. '40%' or 'speed 2'."""

    def __repr__(self) -> str:
        state = "on" if self._is_on else "off"
        return f"{type(self).__name__}({self.name!r}, {state}, {self.status()})"
```

Three new things in there:

- **`class Device(ABC)`** and **`@abstractmethod`**: a promise. Any class that
  inherits from Device must write its own `power_draw` and `status`, or Python refuses
  to create it. And `Device("x")` itself is refused, because a "device" with no kind makes no sense.
- **`type(self).__name__`**: the name of the object's actual class, so the one
  `__repr__` prints `Light(...)` or `Fan(...)` correctly.
- **`self.status()`** inside `__repr__`: the parent asks the child for the part only the child knows.

**Step 3.** Make `Light` a child of `Device`. Replace your whole `Light` class with:

```python
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
        if not 0 <= value <= 100:
            raise InvalidSetting(f"brightness must be 0-100 %, got {value!r}")
        self._brightness = value

    @property
    def power_draw(self) -> float:
        if not self._is_on:
            return 0.0
        return self.watts * self._brightness / 100

    def status(self) -> str:
        return f"{self._brightness}%"
```

`super().__init__(name, watts)` means "run the parent's setup first". Device sets the
name, watts, switch and meter; then Light adds only its dimmer. Notice what's gone: no
`turn_on`, `toggle`, `run` or `__repr__`. Light inherits all of them. Your `toggle` from
Day 1 now lives in Device, where every device gets it.

**Step 4.** Do the same to `Fan`. Replace the whole class with:

```python
class Fan(Device):
    """A fan with speeds 1 to 3."""

    MAX_SPEED = 3

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
```

**Run:** `uv run pytest -q` → Day 1's 24 tests **still pass**, plus Chunk 1 and Chunk 2.

That's the real test of a refactor: you changed the structure completely, and every old
test still passes, so nothing that used to work is broken. **Commit:**
`git commit -am "Extract Device base class"`

**Try it** (`uv run python`):

```python
from smarthome.devices import Device, Fan
Device("mystery")        # TypeError: can't instantiate abstract class
f = Fan("desk fan")
f.toggle(); f            # toggle came from Device; the repr shows 'speed 1' from Fan
Fan.__mro__              # the lookup order: Fan, then Device, then ABC, then object
```

`__mro__` shows where Python looks for a method: first in `Fan`, then in `Device`. That's inheritance in one line.

---

## Chunk 3: class attributes and one loop for every kind (about 10 min)

**Step 1.** Give each class a `kind` class attribute, a label shared by every object of
that class. It's used on Day 4 for saving. Add one line right under each class's docstring:

```python
    kind = "device"     # in Device
    kind = "light"      # in Light
    kind = "fan"        # in Fan
```

**Step 2.** Export the new classes. Replace `src/smarthome/__init__.py` with:

```python
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
```

**Run:** `uv run pytest -q -k Chunk3` → 4 passed. **Commit.**

**The payoff: polymorphism.** Try this in `uv run python`:

```python
from smarthome import Fan, Light
things = [Light("ceiling", watts=12), Fan("desk fan"), Light("bedside", watts=6)]
for t in things:
    t.turn_on()
sum(t.power_draw for t in things)      # 31.33: each one works out its own
[t.status() for t in things]           # ['100%', 'speed 1', '100%']
```

The loop never asks "are you a light or a fan?" Each object answers in its own way.
This is exactly what `Room.all_off()` will do tomorrow.

---

## Your turn: `Thermostat`

Write `class Thermostat(Device)` at the bottom of `devices.py`, following the
pattern of `Fan`. The spec:

| | |
| --- | --- |
| `kind` | `"thermostat"` |
| Class attributes | `MIN_TEMP = 5.0`, `MAX_TEMP = 30.0` |
| Constructor | `Thermostat(name, watts=1500.0, target=20.0)` |
| Setting | `target` property; the setter refuses anything outside 5–30 with `InvalidSetting`, and stores it as a `float` |
| `power_draw` | the full `watts` when on, `0.0` when off (a heater is either heating or not) |
| `status()` | e.g. `"21.0 °C"` (one decimal place) |

**Run:** `uv run pytest -q -k YourTurn` → 10 passed. Then add `Thermostat` to `__init__.py`
(the import line and `__all__`), and run `uv run pytest -q` for **53 passed**.

<details><summary>Hint 1: the target in the constructor must be checked too</summary>

In `__init__`, set a safe default first, then assign through the property so the
setter checks it:

```python
self._target = 20.0
self.target = target   # goes through your setter
```

</details>

<details><summary>Hint 2: formatting one decimal place</summary>

`f"{self._target:.1f} °C"`. To type the ° sign on Windows, hold **Alt** and type **0176** on the number pad, or just copy it from here.

</details>

**Commit and push:** `git commit -am "Thermostat"` then `git push`.

## What to remember from today

1. **Duplication is the signal** to reach for a parent class.
2. **Parent = what's shared, child = what's different.** `super().__init__()` runs the parent's setup.
3. **Abstract methods are a contract**: every child must fill them in, and the parent can safely call them.
4. **Polymorphism**: the parent's `run()` calls `self.power_draw` and gets the child's version.
5. **A refactor is safe when the old tests still pass.**
