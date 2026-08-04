"""Deterministic rule-based agents.

These play the game with no window and no keyboard, so the simulation can be
exercised thousands of times. They are a correctness harness, not a balance
argument: a high survival rate here says the rules hold together, not that the
game is worth playing.

Every agent is a pure function of game state plus its own seeded RNG, so the
same seed and the same agent always produce the same life.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Callable

from . import actions as actions_mod
from . import config
from .commands import Command, Direction

_DELTA_TO_DIRECTION = {d.delta: d for d in Direction}


def step_toward(game, wanted: Callable) -> Command | None:
    """Breadth-first search for the nearest tile satisfying `wanted`.

    Returns the command for the first step, or None if already standing on such
    a tile or nothing was found.
    """
    start = (game.player.x, game.player.y)
    if wanted(game.world.at(*start)):
        return None

    came: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = deque([start])
    goal = None
    while queue and goal is None:
        x, y = queue.popleft()
        for nx, ny, tile in game.world.neighbours(x, y):
            if (nx, ny) in came:
                continue
            came[(nx, ny)] = (x, y)
            if wanted(tile):
                goal = (nx, ny)
                break
            queue.append((nx, ny))

    if goal is None:
        return None

    node = goal
    while came[node] != start:
        node = came[node]  # type: ignore[assignment]
    delta = (node[0] - start[0], node[1] - start[1])
    direction = _DELTA_TO_DIRECTION.get(delta)
    return Command.move(direction) if direction else None


def _conceivable_keys(game) -> list[str]:
    return [a.key for a in actions_mod.conceivable(game)]


def _has_wood(game) -> bool:
    return game.player.carrying("wood") > 0


def _at_fire(game):
    return game.fires.at(game.player.x, game.player.y)


def _toward_wood(game):
    return step_toward(game, lambda t: t.resources.get("wood", 0) > 0)


def _toward_water(game):
    return step_toward(game, lambda t: t.terrain.drinkable)


def _toward_food(game):
    return step_toward(game, lambda t: t.resources.get("forage", 0) > 0)


def _make_fire(game):
    """Get warm, or take a step toward being able to.

    Every branch here exists because an agent once got stuck repeating a
    refused action forever: standing in the river trying to strike a fire, or
    trying it with hands too tired to hold the tinder. An agent that cannot
    make progress must move or rest, never repeat.
    """
    if _at_fire(game):
        return Command.action("b") if _has_wood(game) else None
    if not _has_wood(game):
        return None
    if game.tile().terrain.drinkable:
        # No fire is ever lit on wet ground. Walk to dry land first.
        return step_toward(game, lambda t: not t.terrain.drinkable)
    if game.player.needs.exhausted:
        return Command.action("r")
    return Command.action("b")


# ---------------------------------------------------------------------------
# 1. Random valid action - the crash finder
# ---------------------------------------------------------------------------

def random_agent(game, rng: random.Random) -> Command:
    if rng.random() < 0.45:
        return Command.move(rng.choice(list(Direction)))
    return Command.action(rng.choice(_conceivable_keys(game)))


# ---------------------------------------------------------------------------
# 2. First-night survival - the one the game is actually about
# ---------------------------------------------------------------------------

def survivor_agent(game, rng: random.Random) -> Command:
    player, needs = game.player, game.player.needs
    fire = _at_fire(game)

    if needs.exhausted:
        return Command.action("s" if (game.clock.is_night and fire) else "r")

    if fire and fire.fuel < config.AGENT_FIRE_TOP_UP_BELOW and _has_wood(game):
        return Command.action("b")

    dusk_soon = game.clock.hour >= config.DUSK_HOUR - config.AGENT_DUSK_LEAD_HOURS
    if game.clock.is_night or dusk_soon:
        if not fire:
            lit = _make_fire(game)
            if lit is not None:
                return lit
        elif needs.rest < config.AGENT_SLEEP_REST_BELOW:
            return Command.action("s")

    if needs.warmth < config.AGENT_COLD_BELOW and not fire:
        return _make_fire(game) or _toward_wood(game) or Command.action("g")

    if needs.water < config.AGENT_THIRSTY_BELOW:
        return _toward_water(game) or Command.action("d")
    if needs.food < config.AGENT_HUNGRY_BELOW:
        return _toward_food(game) or Command.action("f")
    if player.carrying("wood") < config.AGENT_WOOD_TARGET:
        return _toward_wood(game) or Command.action("g")
    if needs.rest < config.AGENT_TIRED_BELOW:
        return Command.action("r")
    if "m" in _conceivable_keys(game):
        return Command.action("m")
    return Command.action("r")


# ---------------------------------------------------------------------------
# 3. Fire-focused - hoards wood, never leaves the hearth
# ---------------------------------------------------------------------------

def fire_agent(game, rng: random.Random) -> Command:
    needs = game.player.needs
    fire = _at_fire(game)

    if needs.exhausted:
        if fire and game.clock.is_night:
            return Command.action("s")
        return Command.action("r")
    if needs.water < config.AGENT_THIRSTY_BELOW:
        return _toward_water(game) or Command.action("d")
    if needs.food < config.AGENT_HUNGRY_BELOW:
        return _toward_food(game) or Command.action("f")
    return _make_fire(game) or _toward_wood(game) or Command.action("g")


# ---------------------------------------------------------------------------
# 4. Exploration-focused - walks, and keeps walking
# ---------------------------------------------------------------------------

def explorer_agent(game, rng: random.Random) -> Command:
    needs = game.player.needs
    if needs.exhausted:
        return Command.action("r")
    if needs.water < config.AGENT_THIRSTY_BELOW:
        return _toward_water(game) or Command.action("d")
    if needs.food < config.AGENT_HUNGRY_BELOW:
        return _toward_food(game) or Command.action("f")
    return step_toward(game, lambda t: not t.seen) or Command.move(
        rng.choice(list(Direction)))


# ---------------------------------------------------------------------------
# 5. Stillness-focused - tends the spirit and little else
# ---------------------------------------------------------------------------

def still_agent(game, rng: random.Random) -> Command:
    needs = game.player.needs
    if needs.exhausted:
        return Command.action("r")
    if needs.water < config.AGENT_THIRSTY_BELOW:
        return _toward_water(game) or Command.action("d")
    if needs.food < config.AGENT_HUNGRY_BELOW:
        return _toward_food(game) or Command.action("f")
    if needs.warmth < config.AGENT_COLD_BELOW:
        return _make_fire(game) or _toward_wood(game) or Command.action("g")
    if "m" in _conceivable_keys(game):
        return Command.action("m")
    return Command.action("r")


# ---------------------------------------------------------------------------
# 6. Bare subsistence - the point of the whole design.
#    Water, food, warmth, sleep. Nothing else. It should work, and it should
#    hollow the character out.
# ---------------------------------------------------------------------------

def subsistence_agent(game, rng: random.Random) -> Command:
    needs = game.player.needs

    if needs.water < config.AGENT_THIRSTY_BELOW:
        return _toward_water(game) or Command.action("d")
    if needs.food < config.AGENT_HUNGRY_BELOW:
        return _toward_food(game) or Command.action("f")
    if needs.warmth < config.AGENT_COLD_BELOW:
        return _make_fire(game) or _toward_wood(game) or Command.action("g")
    if game.clock.is_night:
        return Command.action("s")
    return Command.action("r")


AGENTS: dict[str, Callable] = {
    "random": random_agent,
    "survivor": survivor_agent,
    "fire": fire_agent,
    "explorer": explorer_agent,
    "still": still_agent,
    "subsistence": subsistence_agent,
}
