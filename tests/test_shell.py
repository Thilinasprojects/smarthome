"""Day 5 tests: the dashboard and the command prompt.

uv run pytest -q -k Chunk1   (then Chunk2, YourTurn)
The Chunk 2 test is skipped until you've run `uv add rich`.
"""

import pytest

try:
    from smarthome.shell import HomeShell, demo_home, demo_scenes
except ImportError:  # shell.py still a stub: skip this file instead of stopping every test
    pytest.skip("shell.py isn't written yet (Chunk 1)", allow_module_level=True)


@pytest.fixture
def shell():
    return HomeShell(demo_home(), demo_scenes())


# ------------------------------------------------------------ Chunk 1: commands
class TestChunk1Commands:
    def test_switch_on(self, shell):
        reply = shell.execute("living ceiling on")
        assert reply == "Light('ceiling', on, 100%)"
        assert shell.home.find("living", "ceiling").is_on

    def test_toggle(self, shell):
        shell.execute("bedroom heater toggle")
        assert shell.home.find("bedroom", "heater").is_on

    def test_change_a_setting(self, shell):
        assert shell.execute("living ceiling brightness 40") == "Light('ceiling', off, 40%)"
        assert shell.execute("bedroom heater target 21.5").endswith("21.5 °C)")

    def test_errors_become_messages(self, shell):
        assert shell.execute("living ceiling brightness 150").startswith("Error:")
        assert shell.execute("garage light on").startswith("Error:")
        assert shell.execute("living ceiling colour 3").startswith("Error:")

    def test_nonsense_is_handled(self, shell):
        assert shell.execute("dance") == "Didn't understand that. Type 'help'."
        assert shell.execute("living ceiling wobble") == "Didn't understand that. Type 'help'."
        assert shell.execute("") == ""

    def test_all_off(self, shell):
        shell.execute("living ceiling on")
        assert shell.execute("all off") == "Everything is off."
        assert not any(d.is_on for d in shell.home.devices())

    def test_run_and_bill(self, shell):
        shell.execute("bedroom heater on")
        assert "3.000 kWh" in shell.execute("run 2")
        assert shell.execute("bill 0.25") == "Bill: 0.75 at 0.25 per kWh"

    def test_scene(self, shell):
        assert shell.execute("scene movie") == "Scene 'movie' applied."
        assert shell.home.find("living", "ceiling").brightness == 20
        assert shell.execute("scene party").startswith("Error:")

    def test_status_and_help(self, shell):
        assert shell.execute("status").startswith("My flat")
        assert "Commands:" in shell.execute("help")


# ------------------------------------------------------------ Chunk 2: the dashboard
class TestChunk2Dashboard:
    def test_table_has_a_row_per_device(self):
        pytest.importorskip("rich")
        from smarthome.dashboard import build_table

        table = build_table(demo_home())
        assert table.row_count == 4
        assert "My flat" in str(table.title)


# ------------------------------------------------------------ Your turn: two new commands
class TestYourTurn:
    def test_energy(self, shell):
        shell.execute("bedroom heater on")
        shell.execute("run 1")
        assert shell.execute("energy") == "Total energy: 1.500 kWh"

    def test_rooms(self, shell):
        assert shell.execute("rooms") == "living (2), bedroom (2)"
