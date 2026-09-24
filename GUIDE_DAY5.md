# Day 5: talk to your house

The model is finished. Today you give it a face: a command prompt where you type
`bedroom heater on`, and a colourful status table. By the end, `uv run smarthome` starts
your own smart home app.

## Setup (2 min)

```powershell
cd C:\code\projects\smarthome
Expand-Archive -Path $HOME\Downloads\smarthome-day5.zip -DestinationPath C:\code\projects -Force
uv run pytest -q
```

The zip adds two stub files (`shell.py`, `dashboard.py`), the guide and the tests. **Extract it once only**, at the start of the day: extracting again would reset the stub file over your work.
The 96 earlier tests pass; today's show as errors until Chunk 1 exists.

## The design: logic separate from the screen

```
  keyboard ──► HomeShell.run()          the ONLY part that uses input() and print()
                   │  one line of text
                   ▼
               HomeShell.execute(line)   pure logic: text in, text out  ◄── the tests call this
                   │  first word
                   ▼
               self.commands  = {"run": self.cmd_run, "bill": self.cmd_bill, ...}
                   │                 a dispatch table: word → method
                   ▼
               cmd_run(args) ──► home.run(hours)      your Day 1–4 code does the real work
               device_command ──► home.find(...) ──► device.turn_on() / setattr(...)

  dashboard.show(home) ──► reads home.rooms, device.status(), power_draw   (only reads)
```

Two rules make this easy to test and change:

1. **`execute` never prints and never reads the keyboard.** It takes text and returns text,
   so the tests can call it directly, no typing needed.
2. **The home knows nothing about the shell or the dashboard.** You could swap the
   terminal for a web page tomorrow without touching a single device.

---

## Chunk 1: the command interpreter (about 25 min)

Replace everything in `src/smarthome/shell.py` with:

```python
"""A command prompt for the home: type `bedroom heater on`.

The logic (execute) is separate from the keyboard and screen (run), so it can be tested.
"""

from pathlib import Path

from smarthome.devices import Fan, Light, Thermostat
from smarthome.errors import InvalidSetting, SmartHomeError
from smarthome.home import Home
from smarthome.scenes import Scene

HELP = """Commands:
  <room> <device> on | off | toggle      e.g.  living ceiling on
  <room> <device> <setting> <value>      e.g.  living ceiling brightness 40
  all off                                every device off
  run <hours>                            let time pass
  bill <price per kWh>                   what the energy has cost
  scene <name>                           apply a scene
  energy                                 total energy used
  rooms                                  list rooms
  status                                 show every device
  save <file> | quit"""


def _number(text: str) -> int | float:
    """'40' -> 40, '21.5' -> 21.5 (raises ValueError for anything else)."""
    return int(text) if text.lstrip("-").isdigit() else float(text)


class HomeShell:
    def __init__(self, home: Home, scenes: list[Scene] | None = None):
        self.home = home
        self.scenes = {scene.name: scene for scene in scenes or []}
        # Dispatch table: first word -> the method that handles it.
        self.commands = {
            "help": self.cmd_help,
            "status": self.cmd_status,
            "all": self.cmd_all,
            "run": self.cmd_run,
            "bill": self.cmd_bill,
            "scene": self.cmd_scene,
            "save": self.cmd_save,
        }

    def execute(self, line: str) -> str:
        """Run one command and return the reply as text."""
        words = line.split()
        if not words:
            return ""
        command, args = words[0].lower(), words[1:]
        try:
            if command in self.commands:
                return self.commands[command](args)
            return self.device_command(words)
        except SmartHomeError as err:
            return f"Error: {err}"
        except (ValueError, IndexError):
            return "Didn't understand that. Type 'help'."

    # ---- one method per command
    def cmd_help(self, args: list[str]) -> str:
        return HELP

    def cmd_status(self, args: list[str]) -> str:
        return self.home.report()

    def cmd_all(self, args: list[str]) -> str:
        if args != ["off"]:
            raise ValueError("expected 'all off'")
        self.home.all_off()
        return "Everything is off."

    def cmd_run(self, args: list[str]) -> str:
        hours = _number(args[0])
        self.home.run(hours)
        return f"{hours} h passed. Energy so far: {self.home.energy_kwh:.3f} kWh"

    def cmd_bill(self, args: list[str]) -> str:
        price = _number(args[0])
        return f"Bill: {self.home.bill(price):.2f} at {price} per kWh"

    def cmd_scene(self, args: list[str]) -> str:
        name = " ".join(args)
        if name not in self.scenes:
            raise InvalidSetting(f"no scene called {name!r}")
        self.home.apply(self.scenes[name])
        return f"Scene '{name}' applied."

    def cmd_save(self, args: list[str]) -> str:
        path = Path(args[0])
        self.home.save(path)
        return f"Saved to {path}"

    def device_command(self, words: list[str]) -> str:
        room, name, action, *rest = words
        device = self.home.find(room, name)
        if not rest:
            switches = {"on": device.turn_on, "off": device.turn_off, "toggle": device.toggle}
            if action not in switches:
                raise ValueError(action)
            switches[action]()
        else:
            if action not in device.settings():
                raise InvalidSetting(f"{name} has no setting {action!r}")
            setattr(device, action, _number(rest[0]))
        return repr(device)


def demo_home() -> Home:
    """A ready-made flat with one-word names, easy to type at the prompt."""
    home = Home("My flat")
    living = home.add_room("living")
    living.add(Light("ceiling", watts=12))
    living.add(Fan("fan", watts=40))
    bedroom = home.add_room("bedroom")
    bedroom.add(Light("bedside", watts=6))
    bedroom.add(Thermostat("heater", watts=1500))
    return home


def demo_scenes() -> list[Scene]:
    movie = Scene("movie").add("living", "ceiling", "on").add("living", "ceiling", "brightness", 20)
    night = Scene("night").add("living", "ceiling", "off").add("living", "fan", "off")
    night.add("bedroom", "bedside", "off").add("bedroom", "heater", "target", 18)
    return [movie, night]
```

The ideas worth slowing down for:

- **The dispatch table** (`self.commands`). Instead of a long `if word == "run": ... elif word == "bill": ...`,
  a dict maps each word to a method. `self.commands[command](args)` looks up the method and calls it.
  Adding a command becomes one method plus one line in the dict. You'll do exactly that in Your Turn.
  (Notice `self.cmd_run`, without brackets: that's the method itself, stored to call later.)
- **One `try` catches every smart-home error.** Your named errors from Day 1 pay off here:
  `except SmartHomeError` turns any of them into a friendly `Error: ...` message instead of a crash.
- **`room, name, action, *rest = words`** unpacks the list. `*rest` collects whatever's
  left over: nothing for `living ceiling on`, or `["40"]` for `living ceiling brightness 40`.
  Too few words raises `ValueError`, which `execute` also catches.
- **Room and device names are one word here** (`living`, `ceiling`), because the prompt
  splits on spaces. That's why the demo flat uses short names.

**Run:** `uv run pytest -q -k Chunk1` → 9 passed. **Commit.**

**Try it** (`uv run python`):

```python
from smarthome.shell import HomeShell, demo_home, demo_scenes
sh = HomeShell(demo_home(), demo_scenes())
print(sh.execute("living ceiling on"))
print(sh.execute("living ceiling brightness 150"))
print(sh.execute("scene movie"))
print(sh.execute("status"))
```

---

## Chunk 2: a colourful dashboard (about 10 min)

**Step 1.** Add a library to the project. This is how you'll add every library from now on:

```powershell
uv add rich
```

Open `pyproject.toml`: `rich` is now listed under `dependencies`. That's the project's
shopping list, so anyone who clones your repo gets it with `uv sync`.

**Step 2.** Replace everything in `src/smarthome/dashboard.py` with:

```python
"""A colourful status table in the terminal, using the `rich` library.

Only this file knows about the screen. The home itself never imports it.
"""

from rich.console import Console
from rich.table import Table

from smarthome.home import Home


def build_table(home: Home) -> Table:
    table = Table(title=f"{home.name} — {home.power_draw:,.1f} W")
    table.add_column("Room", style="cyan")
    table.add_column("Device")
    table.add_column("Kind", style="dim")
    table.add_column("State")
    table.add_column("Setting")
    table.add_column("Power", justify="right")
    for room in home.rooms:
        for device in room:
            state = "[bold green]ON[/]" if device.is_on else "[dim]OFF[/]"
            table.add_row(
                room.name,
                device.name,
                type(device).__name__,
                state,
                device.status(),
                f"{device.power_draw:.1f} W",
            )
    return table


def show(home: Home) -> None:
    Console().print(build_table(home))
```

`rich` understands little colour tags like `[bold green]ON[/]`. Notice this file only
**reads** from the home. It never changes anything.

**Run:** `uv run pytest -q -k Chunk2` → 1 passed. Then see it:

```powershell
uv run python -c "from smarthome.dashboard import show; from smarthome.shell import demo_home; show(demo_home())"
```

**Commit.**

---

## Chunk 3: the app (about 10 min)

**Step 1.** Add the keyboard-and-screen loop to `HomeShell`, just above `def device_command`:

```python
    # ---- the keyboard-and-screen part
    def run(self) -> None:
        print("Smart home. Type 'help', or 'quit' to leave.")
        while True:
            line = input("home> ").strip()
            if line.lower() in ("quit", "exit"):
                break
            if line.lower() == "status":
                from smarthome.dashboard import show  # imported here: only needed on screen

                show(self.home)
            else:
                print(self.execute(line))
```

`while True` repeats until `break`. The `status` command gets the pretty table here,
while `execute("status")` still returns plain text for the tests. The import sits inside
the method so the rest of the shell works even without `rich`.

**Step 2.** Add this function at the very bottom of `shell.py`:

```python
def main() -> None:
    """Entry point for `uv run smarthome`: load home.json if it exists, else the demo flat."""
    saved = Path("home.json")
    home = Home.load(saved) if saved.exists() else demo_home()
    HomeShell(home, demo_scenes()).run()
```

**Step 3.** Make it a real command. Add these lines to `pyproject.toml`, just below the
`dependencies = [...]` block:

```toml
[project.scripts]
smarthome = "smarthome.shell:main"
```

This says: "the command `smarthome` runs the function `main` in `smarthome/shell.py`".

**Step 4.** Install it, then launch your app:

```powershell
uv sync
uv run smarthome
```

Try: `help`, `living ceiling on`, `living ceiling brightness 30`, `bedroom heater on`,
`status`, `run 3`, `bill 0.25`, `scene night`, `status`, `save home.json`, `quit`.
Then run `uv run smarthome` again: it loads `home.json`, so your flat is exactly as you left it.

**Commit.**

---

## Your turn: two new commands

Add two commands to `HomeShell`:

| You type | It replies |
| --- | --- |
| `energy` | `Total energy: 1.500 kWh` (three decimal places) |
| `rooms` | `living (2), bedroom (2)`: each room with its number of devices, joined by `, ` |

Each one is a `cmd_...` method **plus** one line in the `self.commands` dict.

**Run:** `uv run pytest -q -k YourTurn` → 2 passed, then `uv run pytest -q` → **108 passed**.

<details><summary>Hint</summary>

Copy the shape of `cmd_bill`. For `rooms`, build a list of `f"{room.name} ({len(room)})"`
for each room in `self.home.rooms`, then `", ".join(...)` it. `len(room)` works
because of your Day 3 `__len__`.

</details>

---

## Ship it: version 0.1.0

```powershell
uv run ruff format .
uv run ruff check .
git add .
git commit -m "Smart home shell and dashboard"
git tag v0.1.0
git push
git push --tags
```

A **tag** marks a version in the history. On GitHub, open your repo → **Releases** →
**Draft a new release**, pick `v0.1.0`, and describe what it does in two lines.
Your first release.

## What to remember from today

1. **Separate logic from input/output.** `execute` is testable because it never touches the keyboard or screen.
2. **A dispatch table** (a dict of methods) beats a long `if/elif` chain.
3. **Catch your own error family in one place** and turn errors into messages.
4. **`uv add`** puts a library on the shopping list; **`[project.scripts]`** turns a function into a command.
5. **Tags and releases** mark a finished version.

## Look back at the week

You built 5 classes of devices, 2 containers, 2 dataclasses, an error family, a registry,
a save format, a command language and a dashboard, all backed by 108 tests. Open the
project brief's concept map: you've now used every concept in it.
