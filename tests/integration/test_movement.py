"""Movement, the turn gate, and the input lock."""

from __future__ import annotations

import pytest

from life_creation import config
from life_creation.commands import Command, Direction
from life_creation.outcomes import EventKind
from life_creation.world import TerrainType


def test_a_valid_move_advances_one_tile_and_one_turn(session):
    game = session.game
    x, y = game.player.x, game.player.y
    before = game.clock.minutes

    outcome = session.submit(Command.move(Direction.RIGHT))
    assert outcome is not None and outcome.ok
    assert (game.player.x, game.player.y) == (x + 1, y)
    assert game.clock.minutes == before + config.MOVE_MINUTES
    assert outcome.from_x, outcome.from_y == (x, y)
    assert (outcome.to_x, outcome.to_y) == (x + 1, y)


def test_walking_off_the_map_is_refused_and_costs_nothing(game):
    game.player.x, game.player.y = 0, 5
    before = game.clock.minutes
    outcome = game.submit(Command.move(Direction.LEFT))
    assert not outcome.ok
    assert game.player.x == 0
    assert game.clock.minutes == before
    assert outcome.has(EventKind.BLOCKED)


@pytest.mark.parametrize("direction,delta", [
    (Direction.UP, (0, -1)), (Direction.DOWN, (0, 1)),
    (Direction.LEFT, (-1, 0)), (Direction.RIGHT, (1, 0)),
])
def test_each_direction_moves_exactly_one_tile(game, direction, delta):
    game.player.x, game.player.y = 20, 20
    game.submit(Command.move(direction))
    assert (game.player.x, game.player.y) == (20 + delta[0], 20 + delta[1])


def test_there_is_no_diagonal_movement():
    """The design does not support it, so the command cannot express it."""
    assert {d.value for d in Direction} == {"up", "down", "left", "right"}


def test_wading_a_river_costs_more_time_and_a_great_deal_of_warmth(game):
    target = None
    for y in range(game.world.height):
        for x in range(1, game.world.width):
            if (game.world.at(x, y).terrain.key is TerrainType.WATER
                    and not game.world.at(x - 1, y).terrain.drinkable):
                target = (x - 1, y)
                break
        if target:
            break
    if target is None:
        pytest.skip("no dry tile beside the river")

    game.player.x, game.player.y = target
    game.player.needs.warmth = 100.0
    before = game.clock.minutes

    outcome = game.submit(Command.move(Direction.RIGHT))
    assert outcome.ok
    assert outcome.has(EventKind.WADED)
    assert game.clock.minutes == before + config.WADE_MINUTES
    assert game.player.needs.warmth <= 100.0 - config.WADE_WARMTH_COST + 1


def test_moving_costs_rest(game):
    game.player.needs.rest = 100.0
    game.submit(Command.move(Direction.RIGHT))
    assert game.player.needs.rest < 100.0


def test_moving_reveals_new_ground(game):
    before = game.player.tiles_seen
    game.submit(Command.move(Direction.RIGHT))
    assert game.player.tiles_seen > before


def test_seen_ground_stays_remembered_after_you_leave(session):
    game = session.game
    session.submit(Command.move(Direction.RIGHT))
    session.animation_finished()
    remembered = [(x, y) for (x, y) in game.visible()]
    for _ in range(12):
        session.submit(Command.move(Direction.LEFT))
        session.animation_finished()
    still_seen = [p for p in remembered if game.world.at(*p).seen]
    assert len(still_seen) == len(remembered)


# -- the input lock ---------------------------------------------------------

def test_one_input_produces_exactly_one_turn(session):
    game = session.game
    before = game.clock.minutes
    session.submit(Command.move(Direction.RIGHT))
    assert game.clock.minutes == before + config.MOVE_MINUTES
    assert session.turns == 1


def test_input_is_refused_while_the_screen_is_still_animating(session):
    game = session.game
    session.submit(Command.move(Direction.RIGHT))
    assert session.busy
    assert not session.accepting_input

    x = game.player.x
    minutes = game.clock.minutes
    assert session.submit(Command.move(Direction.RIGHT)) is None
    assert game.player.x == x
    assert game.clock.minutes == minutes
    assert session.turns == 1


def test_input_reopens_when_the_animation_reports_it_is_done(session):
    session.submit(Command.move(Direction.RIGHT))
    session.animation_finished()
    assert session.accepting_input
    assert session.submit(Command.move(Direction.RIGHT)) is not None
    assert session.turns == 2


def test_a_refused_turn_does_not_lock_input(session):
    session.game.player.x = 0
    outcome = session.submit(Command.move(Direction.LEFT))
    assert outcome is not None and not outcome.ok
    assert not session.busy
    assert session.accepting_input


def test_the_dead_take_no_further_turns(session):
    game = session.game
    game.player.needs.health = 0.0
    game.player.needs.death_cause = "cold"
    assert not game.alive
    assert session.submit(Command.move(Direction.RIGHT)) is None


def test_a_restart_is_a_new_life_with_nothing_carried_over(session):
    game = session.game
    game.player.add("wood", 9)
    for _ in range(4):
        session.submit(Command.move(Direction.RIGHT))
        session.animation_finished()

    fresh = session.restart("Second", seed=99)
    assert fresh.game.player.carrying("wood") == 0
    assert fresh.game.clock.minutes == config.DAWN_HOUR * config.MINUTES_PER_HOUR
    assert fresh.turns == 0
    assert fresh.game.player.name == "Second"


# -- presentation timing is presentation only -------------------------------

def test_animation_length_does_not_change_the_simulation(session):
    game = session.game
    outcome = session.submit(Command.move(Direction.RIGHT))
    seconds = session.animation_seconds(outcome)
    minutes = game.clock.minutes
    for _ in range(5):
        session.animation_seconds(outcome)
    assert game.clock.minutes == minutes
    assert seconds == config.MOVE_ANIM_SECONDS
