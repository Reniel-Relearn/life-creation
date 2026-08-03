"""Key bindings.

Input mapping belongs to the presentation layer, so this is the only place that
knows which physical key means which simulation command.

A note on the layout. WASD movement and the old terminal action keys collide
outright: `D` cannot be both "move right" and "drink", and `S` cannot be both
"move down" and "sleep". WASD is kept, because moving is what the player does
most, and the four colliding actions were rebound:

    drink   d -> Q      (quench; `E` also drinks when you are at water)
    sleep   s -> Z

`F`, `G`, `B`, `R` and `M` never collided and did not move. The terminal
debugging front end still uses the original letters - it has no WASD to clash
with - and the on-screen prompts always show the real key, so nothing has to be
memorised either way.
"""

from __future__ import annotations

import arcade

from .. import actions as actions_mod
from ..commands import Direction

MOVEMENT: dict[int, Direction] = {
    arcade.key.UP: Direction.UP,
    arcade.key.DOWN: Direction.DOWN,
    arcade.key.LEFT: Direction.LEFT,
    arcade.key.RIGHT: Direction.RIGHT,
    arcade.key.W: Direction.UP,
    arcade.key.S: Direction.DOWN,
    arcade.key.A: Direction.LEFT,
    arcade.key.D: Direction.RIGHT,
    arcade.key.K: Direction.UP,
    arcade.key.J: Direction.DOWN,
    arcade.key.H: Direction.LEFT,
    arcade.key.L: Direction.RIGHT,
}

# Physical key -> the simulation's action key.
ACTIONS: dict[int, str] = {
    arcade.key.Q: actions_mod.DRINK,
    arcade.key.F: actions_mod.FORAGE,
    arcade.key.G: actions_mod.GATHER,
    arcade.key.B: actions_mod.FIRE,
    arcade.key.R: actions_mod.REST,
    arcade.key.Z: actions_mod.SLEEP,
    arcade.key.M: actions_mod.STILL,
}

# The letter shown on screen for each simulation action key.
DISPLAY_KEY: dict[str, str] = {
    actions_mod.DRINK: "Q",
    actions_mod.FORAGE: "F",
    actions_mod.GATHER: "G",
    actions_mod.FIRE: "B",
    actions_mod.REST: "R",
    actions_mod.SLEEP: "Z",
    actions_mod.STILL: "M",
}

# What `E` reaches for, in order. First one that is currently offered wins.
CONTEXTUAL_ORDER = (
    actions_mod.FIRE,
    actions_mod.DRINK,
    actions_mod.GATHER,
    actions_mod.FORAGE,
)

CONTROLS_HELP: tuple[tuple[str, str], ...] = (
    ("Arrows / WASD / HJKL", "Move one tile - and one turn"),
    ("E", "Do the obvious thing here"),
    ("Q", "Drink"),
    ("F", "Forage"),
    ("G", "Gather deadwood"),
    ("B", "Build a fire, or feed one"),
    ("R", "Rest"),
    ("Z", "Sleep"),
    ("M", "Be still"),
    ("Tab", "Journal"),
    ("Esc", "Pause"),
)


def contextual_action(game) -> str | None:
    """What `E` should do where the character is standing.

    The simulation decides what is offered; this only picks among those.
    """
    offered = {action.key for action in actions_mod.available(game)}
    for key in CONTEXTUAL_ORDER:
        if key in offered:
            return key
    return None
