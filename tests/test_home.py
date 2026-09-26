"""Day 3 tests: Room and Home.

uv run pytest -q -k Chunk1   (then Chunk2, Chunk3, YourTurn)
"""

import pytest

from smarthome import DeviceNotFound, DuplicateDevice, Fan, Light, Thermostat
from smarthome.home import Home, Room


@pytest.fixture
def living():
    room = Room("Living room")
    room.add(Light("ceiling", watts=12))
    room.add(Fan("desk fan", watts=40))
    return room


@pytest.fixture
def flat():
    home = Home("My flat")
    living = home.add_room("Living room")
    living.add(Light("ceiling", watts=12))
    living.add(Fan("desk fan", watts=40))
    bedroom = home.add_room("Bedroom")
    bedroom.add(Light("bedside", watts=6))
    bedroom.add(Thermostat("heater", watts=1500))
    return home


# ------------------------------------------------------------ Chunk 1: a Room
class TestChunk1Room:
    def test_new_room_is_empty(self):
        room = Room("Kitchen")
        assert room.name == "Kitchen"
        assert len(room) == 0

    def test_add_returns_the_device(self):
        room = Room("Kitchen")
        lamp = Light("lamp")
        assert room.add(lamp) is lamp

    def test_len_and_contains(self, living):
        assert len(living) == 2
        assert "ceiling" in living
        assert "sofa" not in living

    def test_lookup_by_name(self, living):
        assert living["ceiling"].name == "ceiling"
        assert isinstance(living["desk fan"], Fan)

    def test_missing_device(self, living):
        with pytest.raises(DeviceNotFound):
            living["sofa"]

    def test_no_duplicate_names(self, living):
        with pytest.raises(DuplicateDevice):
            living.add(Light("ceiling"))
        assert len(living) == 2

    def test_loop_over_devices(self, living):
        assert [d.name for d in living] == ["ceiling", "desk fan"]

    def test_repr(self, living):
        assert repr(living) == "Room('Living room', 2 devices)"


# ------------------------------------------------------------ Chunk 2: a Home
class TestChunk2Home:
    def test_room_all_off_and_power(self, living):
        for d in living:
            d.turn_on()
        assert living.power_draw == pytest.approx(12 + 40 / 3)
        living.all_off()
        assert living.power_draw == 0.0

    def test_add_room_returns_it(self):
        home = Home("My flat")
        room = home.add_room("Kitchen")
        assert isinstance(room, Room)
        assert home["Kitchen"] is room

    def test_no_duplicate_rooms(self, flat):
        from smarthome.errors import DuplicateRoom

        with pytest.raises(DuplicateRoom):
            flat.add_room("Bedroom")

    def test_missing_room(self, flat):
        with pytest.raises(DeviceNotFound):
            flat["Garage"]

    def test_rooms_is_a_tuple(self, flat):
        assert isinstance(flat.rooms, tuple)
        assert [r.name for r in flat.rooms] == ["Living room", "Bedroom"]

    def test_devices_walks_every_room(self, flat):
        assert [d.name for d in flat.devices()] == ["ceiling", "desk fan", "bedside", "heater"]

    def test_all_off_everywhere(self, flat):
        for d in flat.devices():
            d.turn_on()
        flat.all_off()
        assert not any(d.is_on for d in flat.devices())

    def test_total_power(self, flat):
        flat["Bedroom"]["heater"].turn_on()
        flat["Living room"]["ceiling"].turn_on()
        assert flat.power_draw == pytest.approx(1512.0)

    def test_repr(self, flat):
        assert repr(flat) == "Home('My flat', 2 rooms)"


# ------------------------------------------------------------ Chunk 3: the report
class TestChunk3Report:
    def test_report(self, flat):
        ceiling = flat["Living room"]["ceiling"]
        ceiling.turn_on()
        ceiling.brightness = 40
        text = flat.report()
        lines = text.splitlines()
        assert lines[0] == "My flat — total draw 4.8 W"
        assert lines[1].strip() == "Living room"
        assert "ceiling" in lines[2] and "Light" in lines[2] and "ON" in lines[2]
        assert "40%" in lines[2] and lines[2].endswith("4.8 W")
        assert lines[4].strip() == "Bedroom"
        assert len(lines) == 7  # header + 2 rooms + 4 devices


# ------------------------------------------------------------ Your turn: remove() and find()
class TestYourTurn:
    def test_remove_returns_the_device(self, living):
        removed = living.remove("desk fan")
        assert removed.name == "desk fan"
        assert "desk fan" not in living
        assert len(living) == 1

    def test_remove_missing(self, living):
        with pytest.raises(DeviceNotFound):
            living.remove("sofa")

    def test_find(self, flat):
        assert flat.find("Bedroom", "heater").name == "heater"

    def test_find_missing_room_or_device(self, flat):
        with pytest.raises(DeviceNotFound):
            flat.find("Garage", "heater")
        with pytest.raises(DeviceNotFound):
            flat.find("Bedroom", "sofa")
