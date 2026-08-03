"""What the character can see.

Kept here rather than in the renderer, because how far you can see is a rule.
Spirit widens perception (DESIGN.md section 1) and the player is never told
that is happening - so the calculation has to live where the simulation can
reach it and the screen cannot.
"""

from __future__ import annotations

from . import config
from .clock import Phase


def base_radius(phase: Phase) -> int:
    if phase is Phase.NIGHT:
        return config.SIGHT_NIGHT
    if phase in (Phase.DAWN, Phase.DUSK):
        return config.SIGHT_DUSK
    return config.SIGHT_DAY


def spirit_bonus(spirit: float) -> int:
    """A tended spirit widens what you notice. Never announced, never shown."""
    share = max(0.0, min(1.0, spirit / config.SPIRIT_SIGHT_FULL_AT))
    return int(config.SPIRIT_SIGHT_BONUS * share)


def sight_radius(game) -> int:
    radius = base_radius(game.clock.phase)
    radius += game.fires.light_bonus_at(game.player.x, game.player.y)
    radius += spirit_bonus(game.player.needs.spirit)
    return radius


def visible_tiles(game) -> frozenset[tuple[int, int]]:
    """Every tile currently in sight.

    Two sources: what the character can see from where they stand, and anything
    close enough to a lit fire to be picked out of the dark.
    """
    seen: set[tuple[int, int]] = set()
    world = game.world

    def disc(cx: int, cy: int, radius: int) -> None:
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if world.in_bounds(x, y):
                    seen.add((x, y))

    disc(game.player.x, game.player.y, sight_radius(game))
    for fire in game.fires.lit_fires():
        disc(fire.x, fire.y, fire.light_radius)

    return frozenset(seen)
