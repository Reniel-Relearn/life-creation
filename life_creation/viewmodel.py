"""What the interface is allowed to know.

Body is numbers, Soul is a sentence, and Spirit is not here at all. That last
one is the point of this module: the HUD cannot leak a value it was never
handed. There is a test that asserts it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import actions as actions_mod
from . import config
from .clock import Phase


@dataclass(frozen=True)
class BodyReading:
    label: str
    value: float          # 0..100
    condition: str        # a word, for interfaces that would rather not show a number


@dataclass(frozen=True)
class Prompt:
    key: str
    text: str


@dataclass(frozen=True)
class PlayView:
    """A snapshot of one moment, safe to hand to a renderer."""
    name: str
    day: int
    time_text: str
    phase: Phase
    is_night: bool

    x: int
    y: int
    standing_in: str
    at_a_fire: bool

    body: tuple[BodyReading, ...]
    warning: str
    soul_line: str            # prose. There is no soul number in this object.

    inventory: tuple[tuple[str, int], ...]
    prompts: tuple[Prompt, ...]
    log: tuple[str, ...]
    alive: bool

    extra: dict = field(default_factory=dict)


def _condition(value: float) -> str:
    if value >= 80:
        return "good"
    if value >= 55:
        return "fair"
    if value >= 30:
        return "low"
    if value >= 10:
        return "bad"
    return "failing"


def build(game) -> PlayView:
    needs = game.player.needs
    tile = game.tile()

    body = tuple(
        BodyReading(label, value, _condition(value))
        for label, value in (
            ("Water", needs.water),
            ("Food", needs.food),
            ("Warmth", needs.warmth),
            ("Rest", needs.rest),
            ("Health", needs.health),
        )
    )

    prompts = tuple(
        Prompt(action.key, action.prompt(game))
        for action in actions_mod.available(game)
        if action.prompt(game)
    )

    return PlayView(
        name=game.player.name,
        day=game.clock.day,
        time_text=game.clock.clock_text(),
        phase=game.clock.phase,
        is_night=game.clock.is_night,
        x=game.player.x,
        y=game.player.y,
        standing_in=tile.terrain.name,
        at_a_fire=game.fires.at(game.player.x, game.player.y) is not None,
        body=body,
        warning=needs.urgent_warning() or "",
        soul_line=needs.describe_soul(),
        inventory=tuple(sorted(game.player.inventory.items())),
        prompts=prompts,
        log=tuple(game.log[-config.LOG_LINES:]),
        alive=game.player.alive,
    )
