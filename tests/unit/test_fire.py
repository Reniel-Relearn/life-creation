"""Fire: fuel, warmth, light, extinction, and the first one ever lit."""

from __future__ import annotations

import pytest

from life_creation import config
from life_creation.commands import Command
from life_creation.fire import Fire, Hearths
from life_creation.outcomes import EventKind
from life_creation.world import TerrainType
from tests.conftest import FixedRng, force_fire, give_wood, set_time


def _on_dry_ground(game):
    for y in range(game.world.height):
        for x in range(game.world.width):
            if game.world.at(x, y).terrain.key is TerrainType.GRASS:
                game.player.x, game.player.y = x, y
                game.reveal()
                return x, y
    pytest.skip("no grassland in this world")


# -- fuel and burn time -----------------------------------------------------

def test_one_wood_buys_the_configured_burn_time():
    hearths = Hearths()
    fire = hearths.light(1, 1, now=0)
    assert fire.fuel == config.FIRE_FUEL_PER_WOOD


def test_a_fire_burns_down_over_exactly_its_fuel():
    fire = Fire(x=0, y=0, fuel=60.0, lit_at_minute=0)
    assert fire.burn(59, now=59) is False
    assert fire.lit
    assert fire.burn(1, now=60) is True
    assert not fire.lit
    assert fire.fuel == 0.0


def test_burning_out_is_reported_once():
    fire = Fire(x=0, y=0, fuel=10.0, lit_at_minute=0)
    assert fire.burn(10, now=10) is True
    assert fire.burn(10, now=20) is False


def test_feeding_cannot_exceed_the_fuel_ceiling():
    fire = Fire(x=0, y=0, fuel=config.FIRE_MAX_FUEL - 10, lit_at_minute=0)
    fire.feed()
    assert fire.fuel == config.FIRE_MAX_FUEL


def test_fuel_never_goes_negative():
    fire = Fire(x=0, y=0, fuel=5.0, lit_at_minute=0)
    fire.burn(500, now=500)
    assert fire.fuel == 0.0


# -- warmth -----------------------------------------------------------------

def test_a_fire_warms_the_tile_it_burns_on():
    hearths = Hearths()
    hearths.light(5, 5, now=0)
    assert hearths.warmth_at(5, 5) == pytest.approx(config.FIRE_WARMTH_BONUS)


def test_warmth_falls_off_with_distance():
    hearths = Hearths()
    hearths.light(5, 5, now=0)
    near = hearths.warmth_at(6, 5)
    assert 0 < near < hearths.warmth_at(5, 5)


def test_no_warmth_beyond_the_radius():
    hearths = Hearths()
    hearths.light(5, 5, now=0)
    far = config.FIRE_WARMTH_RADIUS + 1
    assert hearths.warmth_at(5 + far, 5) == 0.0


def test_a_dying_fire_gives_less_heat():
    hearths = Hearths()
    fire = hearths.light(5, 5, now=0)
    full = hearths.warmth_at(5, 5)
    fire.fuel = config.FIRE_FUEL_PER_WOOD * 0.25
    assert hearths.warmth_at(5, 5) < full


def test_a_burnt_out_fire_gives_no_heat_and_no_light():
    hearths = Hearths()
    fire = hearths.light(5, 5, now=0)
    fire.fuel = 0.0
    assert hearths.warmth_at(5, 5) == 0.0
    assert hearths.light_bonus_at(5, 5) == 0
    assert hearths.at(5, 5) is None


# -- light ------------------------------------------------------------------

def test_a_fire_extends_sight_within_its_light_radius():
    hearths = Hearths()
    hearths.light(5, 5, now=0)
    assert hearths.light_bonus_at(5, 5) == config.SIGHT_FIRE_BONUS
    edge = config.FIRE_LIGHT_RADIUS
    assert hearths.light_bonus_at(5 + edge, 5) == config.SIGHT_FIRE_BONUS
    assert hearths.light_bonus_at(5 + edge + 1, 5) == 0


def test_a_fire_pushes_the_night_back(game):
    set_time(game, 23)
    _on_dry_ground(game)
    dark = game.sight_radius()
    force_fire(game)
    assert game.sight_radius() > dark


def test_tiles_around_a_fire_are_visible_even_at_night(game):
    set_time(game, 23)
    x, y = _on_dry_ground(game)
    force_fire(game)
    game.reveal()
    assert (x, y) in game.visible()
    assert (x + 1, y) in game.visible()


# -- extinction in the running game -----------------------------------------

def test_a_fire_that_runs_out_while_you_sleep_stops_warming_you(game):
    set_time(game, 22)
    _on_dry_ground(game)
    force_fire(game, fuel=30.0)
    game.player.needs.warmth = 60.0

    game.submit(Command.action("s"))
    assert game.fires.at(game.player.x, game.player.y) is None
    assert game.player.needs.warmth < 60.0


def test_a_well_fed_fire_survives_the_night(game):
    set_time(game, 22)
    _on_dry_ground(game)
    force_fire(game, fuel=config.FIRE_MAX_FUEL)

    outcome = game.submit(Command.action("s"))
    assert outcome.ok
    assert game.fires.at(game.player.x, game.player.y) is not None


def test_going_out_is_announced_when_you_are_there(game):
    _on_dry_ground(game)
    force_fire(game, fuel=5.0)
    outcome = game.submit(Command.action("r"))
    assert outcome.has(EventKind.FIRE_DIED)
    assert any("burned down" in m for m in game.log)


def test_burnt_out_fires_are_not_kept_forever(game):
    _on_dry_ground(game)
    force_fire(game, fuel=1.0)
    game.advance(config.MINUTES_PER_HOUR)
    assert len(game.fires) == 0


# -- the first fire ---------------------------------------------------------

def test_the_first_fire_is_recorded_once_only(game):
    _on_dry_ground(game)
    give_wood(game, 6)
    game.rng = FixedRng(0.0)

    game.submit(Command.action("b"))
    assert game.chronicle.has("first_fire")
    first_day = game.chronicle.day_of("first_fire")

    # Let it die, walk on, and light another.
    game.fires.at(game.player.x, game.player.y).fuel = 0.0
    game.fires.forget_dead()
    game.advance(config.MINUTES_PER_DAY)
    if game.alive:
        game.submit(Command.action("b"))

    marks = [t for _, t in game.chronicle.entries
             if t == "you made fire for the first time"]
    assert len(marks) == 1
    assert game.chronicle.day_of("first_fire") == first_day


def test_the_first_fire_feeds_the_soul(game):
    _on_dry_ground(game)
    give_wood(game, 2)
    game.rng = FixedRng(0.0)
    before = game.player.needs.soul
    game.submit(Command.action("b"))
    assert game.player.needs.soul > before


def test_every_fire_lit_is_counted(game):
    _on_dry_ground(game)
    give_wood(game, 4)
    game.rng = FixedRng(0.0)
    game.submit(Command.action("b"))
    assert game.chronicle.fires_made == 1
    game.fires.at(game.player.x, game.player.y).fuel = 0.0
    game.fires.forget_dead()
    game.submit(Command.action("b"))
    assert game.chronicle.fires_made == 2
