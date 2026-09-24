"""Day 4 tests: energy bill, saving and loading, scenes.

uv run pytest -q -k Chunk1   (then Chunk2, Chunk3, Chunk4)
"""

import json

import pytest

try:
    from smarthome import DeviceNotFound, Fan, InvalidSetting, Light, Thermostat
    from smarthome.devices import Device
    from smarthome.home import Home
except ImportError:  # earlier days not finished yet: skip this file instead of stopping every test
    pytest.skip("Day 4 tests: finish Days 2 and 3 first", allow_module_level=True)


@pytest.fixture
def flat():
    home = Home("My flat")
    living = home.add_room("Living room")
    ceiling = living.add(Light("ceiling", watts=12))
    ceiling.brightness = 40
    ceiling.turn_on()
    fan = living.add(Fan("desk fan", watts=40))
    fan.speed = 3
    bedroom = home.add_room("Bedroom")
    bedroom.add(Light("bedside", watts=6))
    heater = bedroom.add(Thermostat("heater", watts=1500, target=21))
    heater.turn_on()
    return home


# ------------------------------------------------------------ Chunk 1: time, energy, money
class TestChunk1Energy:
    def test_run_meters_every_device(self, flat):
        flat.run(hours=2)
        assert flat.find("Living room", "ceiling").energy_kwh == pytest.approx(4.8 * 2 / 1000)
        assert flat.find("Bedroom", "heater").energy_kwh == pytest.approx(3.0)
        assert flat.find("Bedroom", "bedside").energy_kwh == 0.0

    def test_total_energy(self, flat):
        flat.run(hours=2)
        assert flat.energy_kwh == pytest.approx(3.0 + 0.0096)

    def test_bill_rounds_to_pennies(self, flat):
        flat.run(hours=2)
        assert flat.bill(price_per_kwh=0.25) == 0.75


# ------------------------------------------------------------ Chunk 2: devices to and from dicts
class TestChunk2DeviceData:
    def test_settings(self):
        assert Light("a").settings() == {"brightness": 100}
        assert Fan("b").settings() == {"speed": 1}
        assert Thermostat("c", target=18).settings() == {"target": 18.0}

    def test_to_dict(self, flat):
        ceiling = flat.find("Living room", "ceiling")
        assert ceiling.to_dict() == {
            "kind": "light",
            "name": "ceiling",
            "watts": 12,
            "is_on": True,
            "settings": {"brightness": 40},
        }

    def test_from_dict_builds_the_right_class(self):
        data = {"kind": "fan", "name": "desk fan", "watts": 40, "is_on": True, "settings": {"speed": 3}}
        fan = Device.from_dict(data)
        assert isinstance(fan, Fan)
        assert fan.speed == 3
        assert fan.is_on is True

    def test_round_trip_every_kind(self, flat):
        for original in flat.devices():
            copy = Device.from_dict(original.to_dict())
            assert type(copy) is type(original)
            assert copy.to_dict() == original.to_dict()

    def test_from_dict_still_validates(self):
        data = {"kind": "light", "name": "x", "watts": 10, "is_on": False, "settings": {"brightness": 500}}
        with pytest.raises(InvalidSetting):
            Device.from_dict(data)


# ------------------------------------------------------------ Chunk 3: save and load the whole home
class TestChunk3SaveLoad:
    def test_home_to_dict(self, flat):
        data = flat.to_dict()
        assert data["name"] == "My flat"
        assert [r["name"] for r in data["rooms"]] == ["Living room", "Bedroom"]
        assert len(data["rooms"][0]["devices"]) == 2

    def test_save_writes_json(self, flat, tmp_path):
        path = tmp_path / "home.json"
        flat.save(path)
        assert json.loads(path.read_text(encoding="utf-8"))["name"] == "My flat"

    def test_load_rebuilds_the_home(self, flat, tmp_path):
        path = tmp_path / "home.json"
        flat.save(path)
        loaded = Home.load(path)
        assert isinstance(loaded, Home)
        assert loaded.report() == flat.report()


# ------------------------------------------------------------ Chunk 4: scenes
class TestChunk4Scenes:
    def test_action_is_frozen_data(self):
        from smarthome.scenes import Action

        a = Action("Living room", "ceiling", "brightness", 20)
        assert a == Action("Living room", "ceiling", "brightness", 20)
        with pytest.raises(AttributeError):
            a.value = 99

    def test_scene_add_chains(self):
        from smarthome.scenes import Scene

        scene = Scene("movie").add("Living room", "ceiling", "brightness", 20).add(
            "Living room", "desk fan", "off"
        )
        assert scene.name == "movie"
        assert len(scene) == 2

    def test_apply(self, flat):
        from smarthome.scenes import Scene

        movie = (
            Scene("movie")
            .add("Living room", "ceiling", "brightness", 20)
            .add("Living room", "desk fan", "on")
            .add("Bedroom", "heater", "off")
        )
        flat.apply(movie)
        assert flat.find("Living room", "ceiling").brightness == 20
        assert flat.find("Living room", "desk fan").is_on is True
        assert flat.find("Bedroom", "heater").is_on is False

    def test_apply_checks_every_device_first(self, flat):
        from smarthome.scenes import Scene

        bad = Scene("typo").add("Living room", "ceiling", "off").add("Bedroom", "lamp", "off")
        with pytest.raises(DeviceNotFound):
            flat.apply(bad)
        assert flat.find("Living room", "ceiling").is_on is True  # nothing changed

    def test_apply_rejects_unknown_setting(self, flat):
        from smarthome.scenes import Scene

        with pytest.raises(InvalidSetting):
            flat.apply(Scene("odd").add("Living room", "ceiling", "colour", "red"))
