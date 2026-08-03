"""World generation: determinism, variation, validity, memory."""

from __future__ import annotations

import pytest

from life_creation import config
from life_creation.world import TerrainType, World, new_world

SEEDS = [1, 7, 42, 1234, 99999]


def _fingerprint(world: World) -> list[str]:
    return [world.at(x, y).terrain.key.value
            for y in range(world.height) for x in range(world.width)]


def test_same_seed_produces_the_same_world():
    a, _ = new_world(1234)
    b, _ = new_world(1234)
    assert _fingerprint(a) == _fingerprint(b)


def test_same_seed_produces_the_same_resources():
    a, _ = new_world(77)
    b, _ = new_world(77)
    for y in range(a.height):
        for x in range(a.width):
            assert a.at(x, y).resources == b.at(x, y).resources


def test_same_seed_produces_the_same_spawn():
    a, _ = new_world(2024)
    b, _ = new_world(2024)
    assert a.find_start() == b.find_start()


def test_different_seeds_produce_different_worlds():
    a, _ = new_world(1)
    b, _ = new_world(2)
    assert _fingerprint(a) != _fingerprint(b)


def test_generation_does_not_touch_the_global_random_stream():
    import random

    random.seed(999)
    expected = [random.random() for _ in range(3)]
    random.seed(999)
    new_world(5)
    assert [random.random() for _ in range(3)] == expected


@pytest.mark.parametrize("seed", SEEDS)
def test_generated_worlds_validate(seed):
    world, report = new_world(seed)
    assert report.ok, report.problems


@pytest.mark.parametrize("seed", SEEDS)
def test_spawn_is_on_open_ground_and_in_bounds(seed):
    world, _ = new_world(seed)
    x, y = world.find_start()
    assert world.in_bounds(x, y)
    assert world.at(x, y).terrain.key in (TerrainType.GRASS, TerrainType.FOREST)


@pytest.mark.parametrize("seed", SEEDS)
def test_water_and_forest_are_reachable_from_the_spawn(seed):
    world, _ = new_world(seed)
    x, y = world.find_start()
    assert world.reachable_from(x, y, lambda t: t.terrain.drinkable)
    assert world.reachable_from(x, y, lambda t: t.resources.get("wood", 0) > 0)


@pytest.mark.parametrize("seed", SEEDS)
def test_first_night_resources_are_within_a_days_walk(seed):
    world, report = new_world(seed)
    assert report.water_distance <= config.WORLD_VALIDATE_WATER_WITHIN
    assert report.wood_distance <= config.WORLD_VALIDATE_WOOD_WITHIN


def test_worlds_vary_meaningfully_rather_than_being_normalised():
    """Difficult seeds must survive. Only broken ones are regenerated."""
    distances = {new_world(seed)[1].wood_distance for seed in range(20, 45)}
    assert len(distances) > 1, "every world had identical resource spacing"


def test_bounds_are_enforced():
    world, _ = new_world(3)
    assert world.in_bounds(0, 0)
    assert world.in_bounds(world.width - 1, world.height - 1)
    assert not world.in_bounds(-1, 0)
    assert not world.in_bounds(world.width, 0)
    assert not world.in_bounds(0, world.height)


def test_terrain_resources_are_consistent_with_terrain():
    world, _ = new_world(11)
    for y in range(world.height):
        for x in range(world.width):
            tile = world.at(x, y)
            if tile.terrain.key is TerrainType.WATER:
                assert tile.resources == {}
            if tile.resources.get("wood", 0) > 0:
                assert tile.terrain.key is TerrainType.FOREST
            if tile.resources.get("reeds", 0) > 0:
                assert tile.terrain.key is TerrainType.MARSH
            if tile.resources.get("stone", 0) > 0:
                assert tile.terrain.key is TerrainType.HILLS


def test_taking_a_resource_depletes_it_deterministically():
    world, _ = new_world(11)
    tile = next(world.at(x, y)
                for y in range(world.height) for x in range(world.width)
                if world.at(x, y).resources.get("wood", 0) >= 2)
    before = tile.resources["wood"]
    assert tile.take("wood", 2) == 2
    assert tile.resources["wood"] == before - 2


def test_taking_more_than_is_there_returns_only_what_was_there():
    world, _ = new_world(11)
    tile = world.at(0, 0)
    tile.resources["wood"] = 1
    assert tile.take("wood", 5) == 1
    assert tile.resources["wood"] == 0
    assert tile.take("wood", 5) == 0


def test_tiles_start_unseen_and_remember_being_seen():
    world, _ = new_world(11)
    tile = world.at(4, 4)
    assert tile.seen is False
    tile.seen = True
    assert world.at(4, 4).seen is True


def test_validation_rejects_a_world_with_only_one_terrain():
    world = World(20, 20, seed=1)
    for row in world.tiles:
        for tile in row:
            tile.terrain = world.at(0, 0).terrain
            tile.resources = {}
    report = world.validate(start=(5, 5))
    assert not report.ok
    assert any("terrain types" in p for p in report.problems)


def test_validation_rejects_a_world_with_no_water():
    from life_creation.world import TERRAIN

    world = World(20, 20, seed=2)
    for row in world.tiles:
        for tile in row:
            if tile.terrain.drinkable:
                tile.terrain = TERRAIN[TerrainType.GRASS]
    report = world.validate(start=(5, 5))
    assert not report.ok
    assert any("water" in p for p in report.problems)
