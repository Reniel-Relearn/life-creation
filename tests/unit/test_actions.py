"""Every action: what it requires, what it costs, and what it refuses."""

from __future__ import annotations

import pytest

from life_creation import config, skills
from life_creation.commands import Command
from life_creation.world import TerrainType
from tests.conftest import FixedRng, force_fire, give_wood, put_player_on, set_time


def _stand_beside_water(game):
    for y in range(game.world.height):
        for x in range(game.world.width):
            if game.world.at(x, y).terrain.key is not TerrainType.WATER:
                continue
            for nx, ny, tile in game.world.neighbours(x, y):
                if not tile.terrain.drinkable:
                    game.player.x, game.player.y = nx, ny
                    game.reveal()
                    return nx, ny
    pytest.skip("no dry tile beside water in this world")


def _stand_on(game, predicate):
    for y in range(game.world.height):
        for x in range(game.world.width):
            if predicate(game.world.at(x, y)):
                game.player.x, game.player.y = x, y
                game.reveal()
                return x, y
    pytest.skip("no matching tile in this world")


# -- drink ------------------------------------------------------------------

def test_drink_requires_water_within_reach(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.HILLS)
    for _, _, n in game.world.neighbours(game.player.x, game.player.y):
        if n.terrain.drinkable:
            pytest.skip("this hill tile touches water")
    outcome = game.submit(Command.action("d"))
    assert not outcome.ok
    assert "no water" in outcome.messages[0].lower()


def test_drinking_from_a_neighbouring_tile_works(game):
    _stand_beside_water(game)
    game.player.needs.water = 20.0
    outcome = game.submit(Command.action("d"))
    assert outcome.ok
    assert game.player.needs.water > 20.0


def test_drinking_costs_the_configured_time(game):
    _stand_beside_water(game)
    before = game.clock.minutes
    outcome = game.submit(Command.action("d"))
    assert outcome.minutes == config.DRINK_MINUTES
    assert game.clock.minutes == before + config.DRINK_MINUTES


def test_marsh_water_slakes_less_than_running_water(game):
    running = _stand_on(game, lambda t: t.terrain.key is TerrainType.WATER)
    game.player.needs.water = 0.0
    game.submit(Command.action("d"))
    from_river = game.player.needs.water

    _stand_on(game, lambda t: t.terrain.key is TerrainType.MARSH)
    game.player.needs.water = 0.0
    game.submit(Command.action("d"))
    assert game.player.needs.water < from_river


def test_a_refused_action_costs_no_time(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.HILLS
              and not any(n.terrain.drinkable
                          for _, _, n in game.world.neighbours(0, 0)))
    before = game.clock.minutes
    game.submit(Command.action("d"))
    assert game.clock.minutes in (before, before + config.DRINK_MINUTES)


# -- forage -----------------------------------------------------------------

def test_forage_requires_something_to_find(game):
    _stand_on(game, lambda t: t.resources.get("forage", 0) == 0)
    outcome = game.submit(Command.action("f"))
    assert not outcome.ok
    assert "nothing more to eat" in outcome.messages[0]


def test_foraging_feeds_you_and_depletes_the_tile(game):
    _stand_on(game, lambda t: t.resources.get("forage", 0) > 0)
    tile = game.tile()
    before_food = game.player.needs.food = 40.0
    before_forage = tile.resources["forage"]

    outcome = game.submit(Command.action("f"))
    assert outcome.ok
    assert game.player.needs.food > before_food
    assert tile.resources["forage"] == before_forage - 1


def test_foraging_costs_rest_and_time(game):
    _stand_on(game, lambda t: t.resources.get("forage", 0) > 0)
    game.player.needs.rest = 100.0
    outcome = game.submit(Command.action("f"))
    assert outcome.minutes == config.FORAGE_MINUTES
    assert game.player.needs.rest < 100.0


def test_foraging_is_refused_when_exhausted(game):
    _stand_on(game, lambda t: t.resources.get("forage", 0) > 0)
    game.player.needs.rest = 0.0
    outcome = game.submit(Command.action("f"))
    assert not outcome.ok
    assert "too spent" in outcome.messages[0]


def test_skill_makes_foraging_yield_more(game):
    _stand_on(game, lambda t: t.resources.get("forage", 0) > 2)
    game.rng = FixedRng(0.5)

    game.player.needs.food = 0.0
    game.submit(Command.action("f"))
    unskilled = game.player.needs.food

    game.player.skills[skills.FORAGING] = 1.0
    game.player.needs.food = 0.0
    game.submit(Command.action("f"))
    assert game.player.needs.food > unskilled


def test_foraging_practises_foraging(game):
    _stand_on(game, lambda t: t.resources.get("forage", 0) > 0)
    before = game.player.skills[skills.FORAGING]
    game.submit(Command.action("f"))
    assert game.player.skills[skills.FORAGING] > before


# -- gather -----------------------------------------------------------------

def test_gathering_requires_deadwood(game):
    _stand_on(game, lambda t: t.resources.get("wood", 0) == 0)
    outcome = game.submit(Command.action("g"))
    assert not outcome.ok
    assert "no deadwood" in outcome.messages[0]


def test_gathering_moves_wood_from_the_tile_into_the_pack(game):
    _stand_on(game, lambda t: t.resources.get("wood", 0) >= 2)
    tile = game.tile()
    tile_before = tile.resources["wood"]
    carried_before = game.player.carrying("wood")

    outcome = game.submit(Command.action("g"))
    assert outcome.ok
    taken = carried_before + tile_before - tile.resources["wood"]
    assert game.player.carrying("wood") == taken
    assert tile.resources["wood"] < tile_before


def test_woodcraft_skill_increases_the_haul(game):
    _stand_on(game, lambda t: t.resources.get("wood", 0) >= 6)
    game.player.skills[skills.WOODCRAFT] = 1.0
    game.submit(Command.action("g"))
    assert game.player.carrying("wood") >= config.GATHER_WOOD_BASE + 1


# -- fire -------------------------------------------------------------------

def test_building_a_fire_needs_wood(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.GRASS)
    outcome = game.submit(Command.action("b"))
    assert not outcome.ok
    assert "no wood" in outcome.messages[0].lower()


def test_no_fire_is_lit_on_wet_ground(game):
    _stand_on(game, lambda t: t.terrain.drinkable)
    give_wood(game)
    outcome = game.submit(Command.action("b"))
    assert not outcome.ok
    assert "wet" in outcome.messages[0].lower()


def test_a_successful_strike_lights_a_fire_and_spends_one_wood(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.GRASS)
    give_wood(game, 3)
    game.rng = FixedRng(0.0)                # always catches
    outcome = game.submit(Command.action("b"))
    assert outcome.ok
    assert game.fires.at(game.player.x, game.player.y) is not None
    assert game.player.carrying("wood") == 2


def test_a_failed_strike_costs_the_time_but_not_the_wood(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.GRASS)
    give_wood(game, 3)
    game.rng = FixedRng(0.999)              # never catches
    outcome = game.submit(Command.action("b"))
    assert outcome.ok                       # the attempt happened
    assert game.fires.at(game.player.x, game.player.y) is None
    assert game.player.carrying("wood") == 3
    assert outcome.minutes == config.FIREMAKING_MINUTES


def test_firemaking_skill_improves_the_odds(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.GRASS)
    give_wood(game, 2)
    # A roll that fails at skill zero and succeeds at mastery.
    game.rng = FixedRng(config.FIREMAKING_BASE_CHANCE + 0.1)
    game.submit(Command.action("b"))
    assert game.fires.at(game.player.x, game.player.y) is None

    game.player.skills[skills.FIREMAKING] = 1.0
    game.submit(Command.action("b"))
    assert game.fires.at(game.player.x, game.player.y) is not None


def test_feeding_a_fire_spends_wood_and_buys_burn_time(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.GRASS)
    fire = force_fire(game, fuel=30.0)
    give_wood(game, 1)
    outcome = game.submit(Command.action("b"))
    assert outcome.ok
    assert fire.fuel == pytest.approx(30.0 + config.FIRE_FUEL_PER_WOOD
                                      - config.FEED_FIRE_MINUTES, abs=1.0)
    assert game.player.carrying("wood") == 0


def test_feeding_a_fire_with_no_wood_is_refused(game):
    force_fire(game)
    outcome = game.submit(Command.action("b"))
    assert not outcome.ok
    assert "no wood" in outcome.messages[0].lower()


def test_firemaking_is_refused_when_exhausted(game):
    _stand_on(game, lambda t: t.terrain.key is TerrainType.GRASS)
    give_wood(game)
    game.player.needs.rest = 0.0
    outcome = game.submit(Command.action("b"))
    assert not outcome.ok
    assert "shaking" in outcome.messages[0]


# -- rest, sleep, stillness -------------------------------------------------

def test_resting_returns_rest_and_costs_an_hour(game):
    game.player.needs.rest = 40.0
    outcome = game.submit(Command.action("r"))
    assert outcome.ok
    assert outcome.minutes == config.REST_MINUTES
    assert game.player.needs.rest > 40.0


def test_sleeping_at_night_runs_until_dawn(game):
    set_time(game, 22)
    # A fire, or the sleeper freezes before morning - which is the point of
    # the game, and is covered by its own test in test_fire.py.
    _stand_on(game, lambda t: t.terrain.key is TerrainType.GRASS)
    force_fire(game, fuel=config.FIRE_MAX_FUEL)

    outcome = game.submit(Command.action("s"))
    assert outcome.ok
    assert outcome.minutes == 8 * config.MINUTES_PER_HOUR
    assert game.alive
    assert game.clock.hour == config.DAWN_HOUR


def test_sleeping_in_the_open_on_a_cold_night_can_kill_you(game):
    set_time(game, 22)
    _stand_on(game, lambda t: t.terrain.key is TerrainType.HILLS)
    game.player.needs.warmth = 20.0

    outcome = game.submit(Command.action("s"))
    assert outcome.ok
    assert not game.alive
    assert game.player.needs.death_cause == "cold"


def test_sleep_never_runs_past_its_maximum(game):
    set_time(game, 19)
    outcome = game.submit(Command.action("s"))
    assert outcome.minutes == config.SLEEP_MAX_HOURS * config.MINUTES_PER_HOUR


def test_sleeping_in_daylight_is_shorter(game):
    set_time(game, 10)
    outcome = game.submit(Command.action("s"))
    assert outcome.minutes == config.SLEEP_DAYTIME_HOURS * config.MINUTES_PER_HOUR


def test_sleeping_does_not_cost_rest(game):
    set_time(game, 22)
    game.player.needs.rest = 20.0
    game.submit(Command.action("s"))
    assert game.player.needs.rest > 20.0


def test_being_still_costs_time_and_returns_nothing_visible(game):
    before_food = game.player.needs.food
    outcome = game.submit(Command.action("m"))
    assert outcome.ok
    assert outcome.minutes == config.STILL_MINUTES
    assert game.player.needs.food < before_food     # time passed, as it always does


def test_being_still_practises_stillness(game):
    before = game.player.skills[skills.STILLNESS]
    game.submit(Command.action("m"))
    assert game.player.skills[skills.STILLNESS] > before


def test_an_unknown_action_key_does_nothing(game):
    before = game.clock.minutes
    outcome = game.submit(Command.action("!"))
    assert not outcome.ok
    assert game.clock.minutes == before
