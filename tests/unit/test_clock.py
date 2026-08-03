"""The clock: advancement, day rollover, phases, sleep, debug acceleration."""

from __future__ import annotations

import pytest

from life_creation import config
from life_creation.clock import Clock, Phase


def test_wakes_at_dawn_on_day_one():
    clock = Clock()
    assert clock.day == 1
    assert clock.hour == config.DAWN_HOUR
    assert clock.phase is Phase.DAWN


def test_advance_moves_absolute_time():
    clock = Clock()
    start = clock.minutes
    clock.advance(90)
    assert clock.minutes == start + 90
    assert clock.hour == config.DAWN_HOUR + 1
    assert clock.minute == 30


def test_day_rolls_over_at_midnight_not_at_dawn():
    clock = Clock()
    clock.advance(config.MINUTES_PER_DAY - clock.minutes - 1)
    assert clock.day == 1
    clock.advance(1)
    assert clock.day == 2
    assert clock.minute_of_day == 0


@pytest.mark.parametrize("hour,expected", [
    (0, Phase.NIGHT), (3, Phase.NIGHT),
    (5, Phase.DAWN), (6, Phase.DAWN),
    (8, Phase.DAY), (12, Phase.DAY), (16, Phase.DAY),
    (17, Phase.DUSK), (18, Phase.DUSK),
    (19, Phase.NIGHT), (23, Phase.NIGHT),
])
def test_phase_classification(hour, expected):
    clock = Clock(minutes=hour * config.MINUTES_PER_HOUR)
    assert clock.phase is expected


@pytest.mark.parametrize("hour,night", [
    (0, True), (5, True), (6, False), (12, False), (17, False),
    (18, True), (22, True),
])
def test_is_night_matches_the_working_day(hour, night):
    assert Clock(minutes=hour * config.MINUTES_PER_HOUR).is_night is night


def test_step_is_a_variable_not_a_constant():
    """The widening time step depends on this being writable from day one."""
    clock = Clock()
    assert clock.step == config.DEFAULT_STEP_MINUTES
    clock.step = 60
    assert clock.step == 60
    assert Clock().step == config.DEFAULT_STEP_MINUTES


def test_minutes_until_dawn_crosses_midnight():
    clock = Clock(minutes=22 * config.MINUTES_PER_HOUR)
    assert clock.minutes_until_dawn() == 8 * config.MINUTES_PER_HOUR


def test_minutes_until_dawn_wraps_a_whole_day_when_it_is_already_dawn():
    clock = Clock(minutes=config.DAWN_HOUR * config.MINUTES_PER_HOUR)
    assert clock.minutes_until_dawn() == config.MINUTES_PER_DAY


def test_night_is_colder_than_afternoon():
    afternoon = Clock(minutes=15 * config.MINUTES_PER_HOUR)
    before_dawn = Clock(minutes=3 * config.MINUTES_PER_HOUR)
    assert afternoon.ambient_temperature() > before_dawn.ambient_temperature()
    assert afternoon.ambient_temperature() == pytest.approx(config.TEMP_DAY, abs=0.01)
    assert before_dawn.ambient_temperature() == pytest.approx(config.TEMP_NIGHT,
                                                              abs=0.01)


# -- debug acceleration -----------------------------------------------------

def test_time_scale_defaults_to_off():
    """Acceleration must never be reachable by accident during normal play."""
    assert Clock().scale == 1.0
    assert Clock().scaled(10) == 10


def test_time_scale_multiplies_only_when_asked():
    assert Clock(scale=20.0).scaled(10) == 200.0


def test_time_scale_is_isolated_from_the_stored_time():
    """Scaling changes what a turn costs, never what the clock already reads."""
    clock = Clock(scale=20.0)
    before = clock.minutes
    clock.advance(10)
    assert clock.minutes == before + 10
