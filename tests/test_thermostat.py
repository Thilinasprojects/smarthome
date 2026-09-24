"""Day 2, your turn: write Thermostat yourself.   uv run pytest -q -k YourTurn"""

import pytest

from smarthome import InvalidSetting
try:
    from smarthome.devices import Device, Thermostat
except ImportError:  # not written yet: skip this file instead of stopping every test
    pytest.skip("Thermostat isn't written yet (Your Turn)", allow_module_level=True)


class TestYourTurnThermostat:
    def test_is_a_device(self):
        assert isinstance(Thermostat("heater"), Device)
        assert Thermostat.kind == "thermostat"

    def test_defaults(self):
        t = Thermostat("heater")
        assert t.watts == 1500.0
        assert t.target == 20.0
        assert t.is_on is False

    def test_target_in_constructor(self):
        assert Thermostat("heater", target=18).target == 18.0

    @pytest.mark.parametrize("bad", [4.9, 30.1, -10])
    def test_rejects_bad_target(self, bad):
        t = Thermostat("heater")
        with pytest.raises(InvalidSetting):
            t.target = bad
        assert t.target == 20.0

    def test_rejects_bad_target_in_constructor(self):
        with pytest.raises(InvalidSetting):
            Thermostat("heater", target=45)

    def test_limits_are_class_attributes(self):
        assert Thermostat.MIN_TEMP == 5.0
        assert Thermostat.MAX_TEMP == 30.0

    def test_power_is_full_watts_when_on(self):
        t = Thermostat("heater", watts=1500)
        assert t.power_draw == 0.0
        t.turn_on()
        assert t.power_draw == 1500.0

    def test_status_and_repr(self):
        t = Thermostat("heater", target=21)
        assert t.status() == "21.0 °C"
        assert repr(t) == "Thermostat('heater', off, 21.0 °C)"
