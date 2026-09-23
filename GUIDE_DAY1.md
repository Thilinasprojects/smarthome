# Day 1: the Light

Today you build one class, `Light`, completely. It's the first box on the project map,
and tomorrow it becomes the model for every other device.

**How today works:** type each chunk into `src/smarthome/devices.py`, run its tests,
try the experiment, commit. There are three chunks, then one small piece you write yourself.

## First, set up (5 min)

```powershell
cd C:\code\projects\smarthome
uv sync
code .
uv run pytest -q          # 24 failed: the starting line
git init
git add .
git commit -m "Start smarthome: Day 1 starter"
```

In VS Code: **Ctrl + Shift + P** → **Python: Select Interpreter** → pick the one with `.venv`.

## The design, in one picture

```
Light
  knows:  name, watts, is_on, brightness (0–100 %), energy_kwh
  does:   turn_on(), turn_off(), toggle(), run(hours)
  works out: power_draw (watts x brightness, or 0 when off)
```

A real smart bulb is exactly this: a name in the app, a rated wattage on the box,
a switch, a dimmer, and a meter counting what it's used.

**How its methods talk to each other.** You (outside) only use the left column.
Only methods touch the stored data in the middle.

```
  YOU CALL                  METHOD DOES                      STORED DATA
  ────────                  ───────────                      ───────────
  light.turn_on()     ───►  sets True               ───►     _is_on
  light.turn_off()    ───►  sets False              ───►     _is_on
  light.toggle()      ───►  calls turn_on() or turn_off()    (via those two)

  light.brightness = 40 ─►  setter: check 0–100,
                            refuse or store         ───►     _brightness

  light.power_draw    ───►  reads _is_on, _brightness, watts
                            returns watts x % (0 if off)

  light.run(hours=3)  ───►  asks power_draw  ───►  adds W x h / 1000  ───► _energy_kwh

  light.energy_kwh    ───►  reads                            _energy_kwh
  print(light)        ───►  __repr__ reads                   _is_on, _brightness
```

Two rules to spot in the picture: **each piece of data has exactly one door in**,
and **methods reuse each other** (`toggle` uses `turn_on`/`turn_off`, `run` uses
`power_draw`) instead of repeating logic. The project brief has the same map
drawn for Days 2–4.

---

## Chunk 1: build it and switch it (about 10 min)

Replace the whole stub `class Light:` in `devices.py` with this:

```python
class Light:
    """A dimmable light."""

    def __init__(self, name: str, watts: float = 10.0):
        # __init__ runs once, when you write Light("ceiling"). Its job: set the new
        # object up in a valid starting state, or refuse to create it at all.
        if watts <= 0:
            raise InvalidSetting(f"watts must be > 0, got {watts!r}")

        self.name = name        # public: anyone may read or rename it
        self.watts = watts      # the rated power on the box

        # Leading underscore = private: only the Light's own methods change these.
        self._is_on = False
        self._brightness = 100  # percent
        self._energy_kwh = 0.0  # the meter

    @property
    def is_on(self) -> bool:
        # A property with no setter: `light.is_on` reads it, `light.is_on = True`
        # is refused. The only way to switch is through the methods below.
        return self._is_on

    def turn_on(self) -> None:
        self._is_on = True

    def turn_off(self) -> None:
        self._is_on = False
```

**Run:** `uv run pytest -q -k Chunk1` → 6 passed.

**Why protect `is_on`?** Tomorrow, turning a device on may need to do more, for
example start its timer. If everyone sets `is_on` directly, that extra step gets skipped.
With methods as the only way in, the object stays in charge of itself.

**Commit:** `git add .` then `git commit -m "Light: build and switch"`

---

## Chunk 2: the dimmer and the power draw (about 10 min)

Add these **inside** the class, below `turn_off` (same indentation as `def turn_off`):

```python
    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        # The setter runs when someone writes `light.brightness = 40`.
        # Check first, change after: a refused value leaves the light untouched.
        if not 0 <= value <= 100:
            raise InvalidSetting(f"brightness must be 0-100 %, got {value!r}")
        self._brightness = value

    @property
    def power_draw(self) -> float:
        """Watts being used right now."""
        # Worked out fresh every time it's read, so it can never be out of date.
        if not self._is_on:
            return 0.0
        return self.watts * self._brightness / 100
```

**Run:** `uv run pytest -q -k Chunk2` → 8 passed.

**Why is `power_draw` a property, not a stored number?** Because it depends on
three other things (on/off, watts, brightness). If you stored it, you'd have to
remember to update it every time any of them changed, and one day you'd forget.
Working it out when asked means it's always right.

**Try it** (`uv run python`):

```python
from smarthome import Light
ceiling = Light("ceiling", watts=12)
ceiling.turn_on()
ceiling.brightness = 40
ceiling.power_draw        # 4.8
ceiling.brightness = 150  # InvalidSetting, and brightness is still 40
```

**Commit.**

---

## Chunk 3: the energy meter and a readable print (about 10 min)

Add below `power_draw`:

```python
    @property
    def energy_kwh(self) -> float:
        """Total energy used so far, in kilowatt-hours (what the bill counts)."""
        return self._energy_kwh

    def run(self, hours: float) -> None:
        """Let time pass: add this period's energy to the meter."""
        if hours < 0:
            raise InvalidSetting(f"hours can't be negative, got {hours!r}")
        # watts x hours = watt-hours; divide by 1000 for kilowatt-hours
        self._energy_kwh += self.power_draw * hours / 1000

    def __repr__(self) -> str:
        # What Python shows when you print the object or look at it in the REPL.
        state = "on" if self._is_on else "off"
        return f"Light({self.name!r}, {state}, {self._brightness}%)"
```

**Run:** `uv run pytest -q -k Chunk3` → 7 passed.

Notice `run()` doesn't redo the power maths. It asks `self.power_draw`, so the
rule "off means zero, dimmed means less" lives in one place only.

**The payoff:** `uv run python examples/my_flat.py`

**Commit.**

---

## Your turn: `toggle()`

A toggle is a button that switches the light to whatever it isn't: off becomes on,
and on becomes off. Add a `toggle()` method to `Light` yourself.

**Run:** `uv run pytest -q -k YourTurn` → 3 passed. Then `uv run pytest -q` → **24 passed**.

<details><summary>Hint, if you're stuck after 5 minutes</summary>

Use what already exists: if the light is on, call `self.turn_off()`, otherwise
`self.turn_on()`. That's four lines, or one if you use `not`:
`self._is_on = not self._is_on`. Which is better, and why? (Think about tomorrow:
what if turning on ever needs to do something extra?)

</details>

**Commit:** `git commit -am "Light: toggle"`, then push to GitHub (see below).

---

## First push to GitHub (5 min)

On github.com: **+** → **New repository** → name `smarthome` → leave "Add a README" **unticked** → **Create**.
Paste the three lines GitHub shows under "…or push an existing repository":

```powershell
git remote add origin https://github.com/<you>/smarthome.git
git branch -M main
git push -u origin main
```

Refresh the page: your code, and every commit, is online.

## What to remember from today

1. `__init__` sets up a **valid** starting state, or refuses to build the object.
2. `_private` data plus **properties** means an object controls its own state.
3. A **setter** is the place to validate: check first, change after.
4. **Work things out** (`power_draw`) rather than store copies that can go stale.
5. **Reuse your own methods** (`run` uses `power_draw`, `toggle` uses `turn_on`).
