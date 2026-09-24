"""Day 4, your turn: SmartPlug, written entirely by you.   uv run pytest -q -k YourTurn"""

import pytest

try:
    from smarthome.devices import DEVICE_TYPES, Device, SmartPlug
    from smarthome.home import Home
except ImportError:  # not written yet: skip this file instead of stopping every test
    pytest.skip("SmartPlug isn't written yet (Your Turn)", allow_module_level=True)


class TestYourTurnSmartPlug:
    def test_is_a_device_with_its_own_kind(self):
        plug = SmartPlug("kettle", watts=2000)
        assert isinstance(plug, Device)
        assert SmartPlug.kind == "plug"

    def test_power(self):
        plug = SmartPlug("kettle", watts=2000)
        assert plug.power_draw == 0.0
        plug.turn_on()
        assert plug.power_draw == 2000

    def test_status_and_settings(self):
        plug = SmartPlug("kettle", watts=2000)
        assert plug.status() == "-"
        assert plug.settings() == {}
        assert repr(plug) == "SmartPlug('kettle', off, -)"

    def test_registered(self):
        assert DEVICE_TYPES["plug"] is SmartPlug

    def test_survives_save_and_load(self, tmp_path):
        home = Home("Test")
        home.add_room("Kitchen").add(SmartPlug("kettle", watts=2000)).turn_on()
        home.save(tmp_path / "h.json")
        loaded = Home.load(tmp_path / "h.json")
        kettle = loaded.find("Kitchen", "kettle")
        assert isinstance(kettle, SmartPlug)
        assert kettle.is_on is True
