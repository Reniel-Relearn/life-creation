"""Soul narrows you. Spirit does nothing you can see. Neither is ever a number
on the screen.
"""

from __future__ import annotations

import pytest

from life_creation import actions as actions_mod
from life_creation import config, viewmodel
from life_creation.commands import Command, Direction
from life_creation.needs import Needs

WARM = config.TEMP_COMFORT + 5


# -- soul -------------------------------------------------------------------

def test_soul_decays_slowly_on_its_own():
    needs = Needs(soul=100.0, spirit=0.0)
    needs.tick(config.SOUL_EMPTY_MINUTES, WARM)
    assert needs.soul == pytest.approx(0.0, abs=1.0)


def test_monotony_costs_soul_beyond_the_threshold(game):
    for _ in range(config.MONOTONY_THRESHOLD + 1):
        game.player.record_action("g")
    penalty = game.player.record_action("g")
    assert penalty > 0


def test_varying_what_you_do_costs_nothing(game):
    assert game.player.record_action("g") == 0.0
    assert game.player.record_action("f") == 0.0
    assert game.player.record_action("g") == 0.0


def test_repetition_beyond_the_threshold_hurts_more_the_longer_it_goes(game):
    penalties = [game.player.record_action("g") for _ in range(12)]
    beyond = [p for p in penalties if p > 0]
    assert beyond == sorted(beyond)
    assert beyond[-1] > beyond[0]


def test_seeing_somewhere_new_feeds_the_soul(session):
    game = session.game
    before = game.player.needs.soul
    seen_before = game.player.tiles_seen
    for _ in range(6):
        session.submit(Command.move(Direction.RIGHT))
        session.animation_finished()
    assert game.player.tiles_seen > seen_before
    # Walking costs time, which costs soul; discovery is what pays it back.
    assert game.player.needs.soul > before - 1.0


def test_surviving_a_night_feeds_the_soul(game):
    from tests.conftest import set_time

    set_time(game, 5, 30)
    game.player.needs.soul = 50.0
    before = game.player.needs.soul
    game.advance(config.MINUTES_PER_HOUR)
    assert game.player.nights_survived == 1
    assert game.player.needs.soul > before


# -- the narrowing ----------------------------------------------------------

def test_stillness_stops_occurring_to_you_when_the_soul_is_low(game):
    game.player.needs.soul = config.SOUL_STILLNESS_LOST_BELOW + 10
    assert "m" in {a.key for a in actions_mod.conceivable(game)}

    game.player.needs.soul = config.SOUL_STILLNESS_LOST_BELOW - 1
    assert "m" not in {a.key for a in actions_mod.conceivable(game)}


def test_the_narrowing_is_silent(game):
    """Nothing is announced. The action simply is not offered."""
    game.player.needs.soul = config.SOUL_STILLNESS_LOST_BELOW - 1
    log_before = list(game.log)
    outcome = game.submit(Command.action("m"))
    assert not outcome.ok
    assert outcome.messages == [""] or outcome.messages == []
    assert game.log == log_before


def test_a_narrowed_action_costs_no_time(game):
    game.player.needs.soul = config.SOUL_STILLNESS_LOST_BELOW - 1
    before = game.clock.minutes
    game.submit(Command.action("m"))
    assert game.clock.minutes == before


def test_the_simulation_decides_the_narrowing_not_the_interface(game):
    """The view model reports prompts; it never filters them itself."""
    game.player.needs.soul = config.SOUL_STILLNESS_LOST_BELOW - 1
    view = viewmodel.build(game)
    assert "m" not in {p.key for p in view.prompts}

    game.player.needs.soul = 90.0
    view = viewmodel.build(game)
    assert "m" in {p.key for p in view.prompts}


# -- spirit -----------------------------------------------------------------

def test_spirit_sustains_the_soul_under_hardship():
    tended = Needs(soul=100.0, spirit=100.0)
    neglected = Needs(soul=100.0, spirit=0.0)
    tended.tick(config.MINUTES_PER_DAY * 30, WARM)
    neglected.tick(config.MINUTES_PER_DAY * 30, WARM)
    assert tended.soul > neglected.soul


def test_neglecting_spirit_carries_no_penalty_of_its_own():
    """It does nothing when neglected. No warning, no damage, no death."""
    empty = Needs(spirit=0.0, health=100.0)
    empty.tick(config.MINUTES_PER_DAY, WARM)
    assert empty.health == 100.0
    assert empty.alive
    assert empty.urgent_warning() is None


def test_spirit_widens_perception(game):
    from life_creation import perception

    assert perception.spirit_bonus(0.0) == 0
    assert perception.spirit_bonus(100.0) == config.SPIRIT_SIGHT_BONUS

    game.player.needs.spirit = 0.0
    narrow = game.sight_radius()
    game.player.needs.spirit = 100.0
    assert game.sight_radius() > narrow


def test_being_still_feeds_spirit(game):
    before = game.player.needs.spirit
    outcome = game.submit(Command.action("m"))
    assert outcome.ok
    assert game.player.needs.spirit > before


# -- what the screen is allowed to see --------------------------------------

def test_the_view_model_contains_no_spirit_value(game):
    game.player.needs.spirit = 73.5
    view = viewmodel.build(game)
    text = repr(view)
    assert "spirit" not in text.lower()
    assert "73.5" not in text
    assert not hasattr(view, "spirit")


def test_the_view_model_contains_no_soul_number(game):
    game.player.needs.soul = 64.0
    view = viewmodel.build(game)
    assert not hasattr(view, "soul")
    assert "64" not in repr(view.body) + view.soul_line
    assert {r.label for r in view.body} == {
        "Water", "Food", "Warmth", "Rest", "Health"}


def test_soul_is_reported_as_prose(game):
    game.player.needs.soul = 30.0
    view = viewmodel.build(game)
    assert view.soul_line
    assert not any(ch.isdigit() for ch in view.soul_line)


def test_spirit_stays_reachable_to_the_simulation_and_to_debug_tools(game):
    """It is hidden from the player, not from the developer."""
    assert 0.0 <= game.player.needs.spirit <= 100.0
