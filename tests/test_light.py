"""Day 1 tests for Light.

Run one chunk at a time:   uv run pytest -q -k Chunk1
Run everything:            uv run pytest -q
"""

import pytest

from smarthome import InvalidSetting, Light


@pytest.fixture
def lamp():
    """A 12 W light, switched on, dimmed to 40 %."""
    light = Light("ceiling", watts=12)
    light.turn_on()
    light.brightness = 40
    return light


# ------------------------------------------------------------ Chunk 1: build and switch
class TestChunk1Basics:
    def test_new_light_defaults(self):
        light = Light("ceiling", watts=12)
        assert light.name == "ceiling"
        assert light.watts == 12
        assert light.is_on is False

    def test_default_watts(self):
        assert Light("hall").watts == 10.0

    @pytest.mark.parametrize("bad_watts", [0, -5])
    def test_rejects_impossible_watts(self, bad_watts):
        with pytest.raises(InvalidSetting):
            Light("broken", watts=bad_watts)

    def test_turn_on_and_off(self):
        light = Light("ceiling")
        light.turn_on()
        assert light.is_on is True
        light.turn_off()
        assert light.is_on is False

    def test_is_on_is_read_only(self):
        light = Light("ceiling")
        with pytest.raises(AttributeError):
            light.is_on = True


# ------------------------------------------------------------ Chunk 2: dimmer and power
class TestChunk2Brightness:
    def test_starts_at_full_brightness(self):
        assert Light("ceiling").brightness == 100

    def test_set_brightness(self, lamp):
        assert lamp.brightness == 40

    @pytest.mark.parametrize("bad", [-1, 101, 150])
    def test_rejects_bad_brightness(self, lamp, bad):
        with pytest.raises(InvalidSetting):
            lamp.brightness = bad
        assert lamp.brightness == 40  # unchanged

    def test_power_draw_scales_with_brightness(self, lamp):
        assert lamp.power_draw == pytest.approx(4.8)  # 12 W x 40 %

    def test_full_brightness_draws_rated_watts(self):
        light = Light("ceiling", watts=12)
        light.turn_on()
        assert light.power_draw == pytest.approx(12.0)

    def test_off_draws_nothing(self, lamp):
        lamp.turn_off()
        assert lamp.power_draw == 0.0


# ------------------------------------------------------------ Chunk 3: energy meter and repr
class TestChunk3Energy:
    def test_meter_starts_at_zero(self):
        assert Light("ceiling").energy_kwh == 0.0

    def test_run_adds_energy(self, lamp):
        lamp.run(hours=3)
        assert lamp.energy_kwh == pytest.approx(0.0144)  # 4.8 W x 3 h = 14.4 Wh

    def test_energy_accumulates(self, lamp):
        lamp.run(hours=1)
        lamp.run(hours=2)
        assert lamp.energy_kwh == pytest.approx(0.0144)

    def test_off_uses_no_energy(self, lamp):
        lamp.turn_off()
        lamp.run(hours=10)
        assert lamp.energy_kwh == 0.0

    def test_rejects_negative_time(self, lamp):
        with pytest.raises(InvalidSetting):
            lamp.run(hours=-1)

    def test_energy_is_read_only(self, lamp):
        with pytest.raises(AttributeError):
            lamp.energy_kwh = 0

    def test_repr(self, lamp):
        assert repr(lamp) == "Light('ceiling', on, 40%)"
        lamp.turn_off()
        assert repr(lamp) == "Light('ceiling', off, 40%)"


# ------------------------------------------------------------ Your turn: toggle()
class TestYourTurnToggle:
    def test_toggle_switches_on(self):
        light = Light("ceiling")
        light.toggle()
        assert light.is_on is True

    def test_toggle_switches_off(self):
        light = Light("ceiling")
        light.turn_on()
        light.toggle()
        assert light.is_on is False

    def test_toggle_twice_is_back_to_start(self):
        light = Light("ceiling")
        light.toggle()
        light.toggle()
        assert light.is_on is False
