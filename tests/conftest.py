"""Shared fixtures.

Tests drive the simulation the same way the game does - through `Session` and
`Command` - so a test passing means the real path works, not a private one.
"""

from __future__ import annotations

import random

import pytest

from life_creation import config
from life_creation.application import Session
from life_creation.game import Game
from life_creation.world import TerrainType

SEED = 1234


@pytest.fixture
def game() -> Game:
    return Game("Tester", SEED)


@pytest.fixture
def session() -> Session:
    return Session("Tester", SEED)


class FixedRng(random.Random):
    """A random source that returns exactly what a test asks it to."""

    def __init__(self, value: float = 0.0, choice_index: int = 0):
        super().__init__(0)
        self.value = value
        self.choice_index = choice_index

    def random(self) -> float:
        return self.value

    def uniform(self, a: float, b: float) -> float:
        return a + (b - a) * self.value

    def choice(self, seq):
        return seq[self.choice_index % len(seq)]


def put_player_on(game: Game, terrain: TerrainType) -> tuple[int, int]:
    """Move the character onto the nearest tile of a given terrain."""
    best = None
    for y in range(game.world.height):
        for x in range(game.world.width):
            if game.world.at(x, y).terrain.key is not terrain:
                continue
            distance = abs(x - game.player.x) + abs(y - game.player.y)
            if best is None or distance < best[0]:
                best = (distance, x, y)
    assert best is not None, f"no {terrain} in this world"
    _, x, y = best
    game.player.x, game.player.y = x, y
    game.reveal()
    return x, y


def give_wood(game: Game, amount: int = 5) -> None:
    game.player.add("wood", amount)


def force_fire(game: Game, fuel: float | None = None):
    """Light a fire under the character without rolling for it."""
    fire = game.fires.light(game.player.x, game.player.y, game.clock.minutes)
    if fuel is not None:
        fire.fuel = fuel
    return fire


def set_time(game: Game, hour: int, minute: int = 0) -> None:
    day_start = (game.clock.day - 1) * config.MINUTES_PER_DAY
    game.clock.minutes = day_start + hour * config.MINUTES_PER_HOUR + minute
    game._was_night = game.clock.is_night
