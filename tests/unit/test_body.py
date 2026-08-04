"""Body: the needs that kill you, and the rates they kill you at."""

from __future__ import annotations

import pytest

from life_creation import config
from life_creation.needs import Needs
from tests.conftest import force_fire, put_player_on, set_time
from life_creation.world import TerrainType

WARM = config.TEMP_COMFORT + 5


def test_water_empties_on_the_rule_of_threes():
    needs = Needs(water=100.0)
    needs.tick(config.WATER_EMPTY_MINUTES, WARM)
    assert needs.water == pytest.approx(0.0, abs=0.5)


def test_food_empties_over_three_weeks():
    needs = Needs(food=100.0)
    needs.tick(config.FOOD_EMPTY_MINUTES, WARM)
    assert needs.food == pytest.approx(0.0, abs=0.5)


def test_warmth_empties_in_three_hours_fully_exposed():
    needs = Needs(warmth=100.0)
    needs.tick(config.WARMTH_EMPTY_MINUTES, config.TEMP_HARSH)
    assert needs.warmth == pytest.approx(0.0, abs=0.5)


def test_decay_scales_with_elapsed_minutes():
    slow = Needs(water=100.0)
    fast = Needs(water=100.0)
    slow.tick(60, WARM)
    fast.tick(120, WARM)
    assert (100 - fast.water) == pytest.approx(2 * (100 - slow.water), rel=1e-6)


def test_warmth_recovers_above_the_comfort_temperature():
    needs = Needs(warmth=20.0)
    needs.tick(60, config.TEMP_COMFORT + 1)
    assert needs.warmth > 20.0


def test_warmth_drains_faster_the_colder_it_is():
    mild = Needs(warmth=100.0)
    harsh = Needs(warmth=100.0)
    mild.tick(60, config.TEMP_COMFORT - 5)
    harsh.tick(60, config.TEMP_HARSH)
    assert (100 - harsh.warmth) > (100 - mild.warmth)


def test_rest_decays_while_awake_and_not_while_resting():
    awake = Needs(rest=100.0)
    resting = Needs(rest=100.0)
    awake.tick(120, WARM)
    resting.tick(120, WARM, resting=True)
    assert awake.rest < 100.0
    assert resting.rest == 100.0


def test_needs_are_held_inside_zero_to_one_hundred():
    needs = Needs(water=100.0, food=100.0)
    needs.water += 500
    needs.food -= 500
    needs.clamp()
    assert needs.water == 100.0
    assert needs.food == 0.0


# -- what actually kills ----------------------------------------------------

def test_freezing_kills_in_about_two_hours():
    needs = Needs(warmth=0.0, health=100.0)
    needs.tick(2 * config.MINUTES_PER_HOUR, config.TEMP_HARSH)
    assert needs.health == 0.0
    assert not needs.alive
    assert needs.death_cause == "cold"


def test_thirst_kills_more_slowly_than_cold():
    cold = Needs(warmth=0.0, health=100.0)
    thirsty = Needs(water=0.0, health=100.0)
    cold.tick(60, config.TEMP_HARSH)
    thirsty.tick(60, WARM)
    assert cold.health < thirsty.health


def test_hunger_kills_most_slowly_of_all():
    thirsty = Needs(water=0.0, health=100.0)
    starving = Needs(food=0.0, health=100.0)
    thirsty.tick(60, WARM)
    starving.tick(60, WARM)
    assert starving.health > thirsty.health


def test_the_cause_of_death_is_the_first_thing_that_was_killing_you():
    needs = Needs(warmth=0.0, water=0.0, health=100.0)
    needs.tick(3 * config.MINUTES_PER_HOUR, config.TEMP_HARSH)
    assert not needs.alive
    assert needs.death_cause == "cold"


def test_health_recovers_only_when_the_body_is_provided_for():
    # Six hours: long enough to see recovery, short enough that the neglected
    # body has not yet run its water down to zero and started taking damage.
    six_hours = 6 * config.MINUTES_PER_HOUR
    provided = Needs(water=90, food=90, warmth=90, health=50)
    neglected = Needs(water=10, food=90, warmth=90, health=50)
    provided.tick(six_hours, WARM)
    neglected.tick(six_hours, WARM)
    assert provided.health > 50
    assert neglected.water > 0, "the neglected body should not be dying yet"
    assert neglected.health == 50


def test_hunger_weakens_long_before_it_kills():
    full = Needs(food=100.0)
    empty = Needs(food=0.0)
    assert empty.vigour < full.vigour
    assert empty.alive


def test_work_costs_more_when_the_body_is_empty(game):
    game.player.needs.food = 100.0
    game.player.needs.rest = 100.0
    game.player.pay_rest(10.0)
    strong_cost = 100.0 - game.player.needs.rest

    game.player.needs.food = 0.0
    game.player.needs.rest = 100.0
    game.player.pay_rest(10.0)
    weak_cost = 100.0 - game.player.needs.rest

    assert weak_cost > strong_cost


# -- shelter and fire, in the running game ----------------------------------

def test_forest_shelters_you_from_the_cold(game):
    set_time(game, 2)
    put_player_on(game, TerrainType.GRASS)
    open_ground = game.effective_temperature()
    put_player_on(game, TerrainType.FOREST)
    assert game.effective_temperature() > open_ground


def test_hills_offer_no_shelter_at_all(game):
    set_time(game, 2)
    put_player_on(game, TerrainType.GRASS)
    grass = game.effective_temperature()
    put_player_on(game, TerrainType.HILLS)
    assert game.effective_temperature() < grass


def test_a_fire_is_worth_more_than_any_terrain(game):
    set_time(game, 2)
    put_player_on(game, TerrainType.GRASS)
    cold = game.effective_temperature()
    force_fire(game)
    assert game.effective_temperature() > cold + config.FIRE_WARMTH_BONUS / 2


def test_dying_is_recorded_once_and_ends_the_run(game):
    game.player.needs.warmth = 0.0
    game.player.needs.health = 1.0
    game.advance(config.MINUTES_PER_HOUR)
    assert not game.alive
    assert game.chronicle.has("death")
    deaths = [t for _, t in game.chronicle.entries if t.startswith("you died")]
    assert len(deaths) == 1
