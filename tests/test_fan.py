"""Day 2 tests: Fan, the Device base class, and polymorphism.

uv run pytest -q -k Chunk1   (then Chunk2, Chunk3)
"""

import pytest

from smarthome import InvalidSetting
from smarthome.devices import Fan, Light


@pytest.fixture
def fan():
    """A 40 W fan, on, at speed 2."""
    f = Fan("desk fan", watts=40)
    f.turn_on()
    f.speed = 2
    return f


# ------------------------------------------------------------ Chunk 1: a Fan
class TestChunk1Fan:
    def test_defaults(self):
        f = Fan("desk fan")
        assert f.name == "desk fan"
        assert f.watts == 40.0
        assert f.is_on is False
        assert f.speed == 1
        assert f.energy_kwh == 0.0

    @pytest.mark.parametrize("bad", [0, 4, -1])
    def test_rejects_bad_speed(self, fan, bad):
        with pytest.raises(InvalidSetting):
            fan.speed = bad
        assert fan.speed == 2

    def test_power_scales_with_speed(self, fan):
        assert fan.power_draw == pytest.approx(40 * 2 / 3)

    def test_off_draws_nothing(self, fan):
        fan.turn_off()
        assert fan.power_draw == 0.0

    def test_run_meters_energy(self, fan):
        fan.run(hours=3)
        assert fan.energy_kwh == pytest.approx(40 * 2 / 3 * 3 / 1000)

    def test_toggle(self):
        f = Fan("desk fan")
        f.toggle()
        assert f.is_on is True

    def test_rejects_impossible_watts(self):
        with pytest.raises(InvalidSetting):
            Fan("broken", watts=0)

    def test_repr(self, fan):
        assert repr(fan) == "Fan('desk fan', on, speed 2)"


# ------------------------------------------------------------ Chunk 2: the Device family
class TestChunk2Device:
    def test_cannot_create_a_plain_device(self):
        from smarthome.devices import Device

        with pytest.raises(TypeError):
            Device("mystery")

    def test_light_and_fan_are_devices(self):
        from smarthome.devices import Device

        assert isinstance(Light("ceiling"), Device)
        assert isinstance(Fan("desk fan"), Device)

    def test_shared_code_lives_in_device(self):
        from smarthome.devices import Device

        # These should be defined once, in Device, and inherited, not copied.
        for method in ("turn_on", "turn_off", "toggle", "run"):
            assert method in vars(Device), f"{method} should be defined in Device"
            assert method not in vars(Light), f"Light should inherit {method}, not copy it"
            assert method not in vars(Fan), f"Fan should inherit {method}, not copy it"

    def test_a_device_must_say_its_power_draw(self):
        from smarthome.devices import Device

        class Broken(Device):
            def status(self):
                return "?"

        with pytest.raises(TypeError):
            Broken("no power_draw")

    def test_light_status(self):
        light = Light("ceiling")
        light.brightness = 40
        assert light.status() == "40%"


# ------------------------------------------------------------ Chunk 3: polymorphism
class TestChunk3Polymorphism:
    def test_kind_class_attribute(self):
        assert Light.kind == "light"
        assert Fan.kind == "fan"
        assert Light("x").kind == "light"  # instances see the class attribute

    def test_max_speed_is_a_class_attribute(self):
        assert Fan.MAX_SPEED == 3

    def test_one_loop_many_kinds(self, fan):
        light = Light("ceiling", watts=12)
        light.turn_on()
        light.brightness = 40
        devices = [light, fan]
        # The loop never asks "is this a light or a fan?" Each answers for itself.
        assert sum(d.power_draw for d in devices) == pytest.approx(4.8 + 40 * 2 / 3)
        assert [d.status() for d in devices] == ["40%", "speed 2"]

    def test_all_off_with_one_loop(self, fan):
        devices = [Light("a"), Light("b"), fan]
        for d in devices:
            d.turn_on()
        for d in devices:
            d.turn_off()
        assert not any(d.is_on for d in devices)
