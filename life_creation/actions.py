"""What you can do with a day.

Every action costs time, and most cost rest. Time is the real currency of the
game: a day spent gathering wood is a day not spent anywhere else.

Each `perform` takes the running game and returns an ActionResult. Actions never
print and never draw - they return data (DESIGN.md section 6, rule 1). Every
random draw comes from `game.rng`, which is seeded from the world seed, so the
same seed and the same choices always produce the same life.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import config, skills
from .outcomes import ActionResult, Event, EventKind

DRINK = "d"
FORAGE = "f"
GATHER = "g"
FIRE = "b"
REST = "r"
SLEEP = "s"
STILL = "m"


@dataclass(frozen=True)
class Action:
    key: str
    label: str
    perform: Callable
    # Whether the character currently thinks of this at all. As Soul falls,
    # actions quietly stop being conceivable. Nothing announces it.
    conceivable: Callable = lambda game: True
    # Whether it is worth offering right now, given where the player is
    # standing. Purely about relevance, never about Soul.
    relevant: Callable = lambda game: True
    # The prompt shown when it is relevant, phrased for the situation.
    prompt: Callable = lambda game: ""


# ---------------------------------------------------------------------------
# Drink - water is the emergency. Three days, and it is over.
# ---------------------------------------------------------------------------

def _water_source(game):
    tile = game.tile()
    if tile.terrain.drinkable:
        return tile.terrain
    for _, _, neighbour in game.world.neighbours(game.player.x, game.player.y):
        if neighbour.terrain.drinkable:
            return neighbour.terrain
    return None


def _drink(game) -> ActionResult:
    source = _water_source(game)
    if source is None:
        return ActionResult(ok=False,
                            messages=["There is no water within reach."])

    gain = config.DRINK_WATER_GAIN
    if source.still_water:
        gain *= config.MARSH_WATER_FACTOR
        note = "You drink from the marsh. It is flat and brackish."
    else:
        note = "You drink until your throat stops aching."

    game.player.needs.water += gain
    game.chronicle.found_water(game.player.x, game.player.y)
    return ActionResult(
        minutes=config.DRINK_MINUTES,
        messages=[note],
        events=[Event(EventKind.DRANK, game.player.x, game.player.y, note)],
    )


# ---------------------------------------------------------------------------
# Forage - food is the strategy. Weeks, not days. It weakens long before it kills.
# ---------------------------------------------------------------------------

def _forage(game) -> ActionResult:
    player, tile = game.player, game.tile()
    if player.needs.exhausted:
        return ActionResult(ok=False, messages=["You are too spent to search."])
    if tile.resources.get("forage", 0) <= 0:
        return ActionResult(
            ok=False,
            messages=[f"You find nothing more to eat in this {tile.terrain.name}."],
        )

    tile.take("forage", 1)
    level = skills.level(player.skills, skills.FORAGING)
    gain = config.FORAGE_FOOD_BASE + config.FORAGE_FOOD_SKILL * level
    gain *= game.rng.uniform(*config.FORAGE_YIELD_SPREAD)
    player.needs.food += gain
    player.pay_rest(config.FORAGE_REST_COST)
    skills.practise(player.skills, skills.FORAGING)

    if gain > config.FORAGE_GOOD_ABOVE:
        msg = "You find roots and a good handful of berries."
    elif gain > config.FORAGE_FAIR_ABOVE:
        msg = "You turn up a few roots. Enough to matter."
    else:
        msg = "You scrape together something thin and bitter."
    return ActionResult(
        minutes=config.FORAGE_MINUTES,
        messages=[msg],
        events=[Event(EventKind.FORAGED, player.x, player.y, msg)],
    )


# ---------------------------------------------------------------------------
# Gather wood - the whole of the early game runs through this
# ---------------------------------------------------------------------------

def _gather(game) -> ActionResult:
    player, tile = game.player, game.tile()
    if player.needs.exhausted:
        return ActionResult(ok=False, messages=["Your arms will not do it."])
    if tile.resources.get("wood", 0) <= 0:
        return ActionResult(ok=False, messages=["There is no deadwood here."])

    level = skills.level(player.skills, skills.WOODCRAFT)
    want = config.GATHER_WOOD_BASE + int(config.GATHER_WOOD_SKILL * level)
    got = tile.take("wood", max(1, want))
    player.add("wood", got)
    player.pay_rest(config.GATHER_REST_COST)
    skills.practise(player.skills, skills.WOODCRAFT)

    total = player.carrying("wood")
    msg = f"You gather {got} wood. You are carrying {total}."
    return ActionResult(
        minutes=config.GATHER_MINUTES,
        messages=[msg],
        events=[Event(EventKind.GATHERED, player.x, player.y, msg)],
    )


# ---------------------------------------------------------------------------
# Fire - the first real gate. Failing to light one as night falls is the game.
# ---------------------------------------------------------------------------

def _fire(game) -> ActionResult:
    player, tile = game.player, game.tile()
    existing = game.fires.at(player.x, player.y)

    if existing is not None:
        if not player.spend("wood", 1):
            return ActionResult(ok=False,
                                messages=["You have no wood to feed it."])
        existing.feed()
        msg = "You feed the fire. It takes the wood gratefully."
        return ActionResult(
            minutes=config.FEED_FIRE_MINUTES,
            messages=[msg],
            events=[Event(EventKind.FIRE_FED, player.x, player.y, msg)],
        )

    if player.carrying("wood") < 1:
        return ActionResult(ok=False, messages=["You have no wood."])
    if player.needs.exhausted:
        return ActionResult(ok=False,
                            messages=["Your hands are shaking too badly."])
    if tile.terrain.drinkable:
        return ActionResult(ok=False, messages=["Not here. The ground is wet."])

    level = skills.level(player.skills, skills.FIREMAKING)
    chance = config.FIREMAKING_BASE_CHANCE + config.FIREMAKING_SKILL_BONUS * level
    player.pay_rest(config.FIREMAKING_REST_COST)
    skills.practise(player.skills, skills.FIREMAKING)

    if game.rng.random() < chance:
        player.spend("wood", 1)
        game.fires.light(player.x, player.y, game.clock.minutes)
        msg = "The tinder catches. You have fire."
        messages = [msg]
        events = [Event(EventKind.FIRE_LIT, player.x, player.y, msg)]
        if not game.chronicle.has("first_fire"):
            game.chronicle.mark("first_fire", game.clock,
                                "you made fire for the first time")
            player.needs.soul += config.SOUL_PER_FIRST_FIRE
            messages.append("Something in you settles.")
        return ActionResult(minutes=config.FIREMAKING_MINUTES,
                            messages=messages, events=events)

    msg = "You work at it until your hands ache. Nothing catches."
    return ActionResult(
        minutes=config.FIREMAKING_MINUTES,
        messages=[msg],
        events=[Event(EventKind.FIRE_FAILED, player.x, player.y, msg)],
    )


# ---------------------------------------------------------------------------
# Rest and sleep
# ---------------------------------------------------------------------------

def _rest(game) -> ActionResult:
    game.player.needs.rest += config.REST_GAIN
    msg = "You sit a while and let your breath come back."
    return ActionResult(
        minutes=config.REST_MINUTES,
        messages=[msg],
        events=[Event(EventKind.RESTED, game.player.x, game.player.y, msg)],
        resting=True,
    )


def _sleep(game) -> ActionResult:
    clock = game.clock
    if clock.is_night:
        minutes = min(clock.minutes_until_dawn(),
                      config.SLEEP_MAX_HOURS * config.MINUTES_PER_HOUR)
    else:
        minutes = config.SLEEP_DAYTIME_HOURS * config.MINUTES_PER_HOUR

    game.player.needs.rest += config.SLEEP_GAIN_PER_MINUTE * minutes
    if game.fires.at(game.player.x, game.player.y):
        opening = "You lie down by the fire."
    elif clock.is_night:
        opening = "You lie down in the dark."
    else:
        opening = "You lie down."
    return ActionResult(
        minutes=minutes,
        messages=[opening],
        events=[Event(EventKind.SLEPT, game.player.x, game.player.y, opening)],
        resting=True,
    )


# ---------------------------------------------------------------------------
# Be still - feeds Spirit. Costs time and returns nothing you can see.
# Disappears below a certain Soul, unannounced. Nothing explains this.
# ---------------------------------------------------------------------------

_STILL_LINES = (
    "You stop, and do nothing, and let the time pass.",
    "You sit still until the noise in your head goes quiet.",
    "You are quiet for a while. Nothing comes of it.",
    "You rest without sleeping, and something in you loosens.",
)


def _be_still(game) -> ActionResult:
    player = game.player
    player.needs.spirit += config.STILL_SPIRIT_GAIN
    skills.practise(player.skills, skills.STILLNESS)
    line = game.rng.choice(_STILL_LINES)
    return ActionResult(
        minutes=config.STILL_MINUTES,
        messages=[line],
        events=[Event(EventKind.STILLED, player.x, player.y, line)],
        resting=True,
    )


def _stillness_still_occurs(game) -> bool:
    return game.player.needs.soul >= config.SOUL_STILLNESS_LOST_BELOW


# ---------------------------------------------------------------------------
# Contextual prompts. Only what is worth offering where you are standing.
# ---------------------------------------------------------------------------

def _drink_prompt(game) -> str:
    source = _water_source(game)
    if source is None:
        return ""
    return f"Drink from the {source.name}"


def _fire_prompt(game) -> str:
    if game.fires.at(game.player.x, game.player.y):
        return "Add wood to the fire"
    return "Build a fire"


def _sleep_prompt(game) -> str:
    return "Sleep until dawn" if game.clock.is_night else "Sleep"


ACTIONS: tuple[Action, ...] = (
    Action(DRINK, "drink", _drink,
           relevant=lambda g: _water_source(g) is not None,
           prompt=_drink_prompt),
    Action(FORAGE, "forage", _forage,
           relevant=lambda g: g.tile().resources.get("forage", 0) > 0,
           prompt=lambda g: "Search the ground for food"),
    Action(GATHER, "gather wood", _gather,
           relevant=lambda g: g.tile().resources.get("wood", 0) > 0,
           prompt=lambda g: "Gather deadwood"),
    Action(FIRE, "build/feed fire", _fire,
           relevant=lambda g: (g.fires.at(g.player.x, g.player.y) is not None
                               or (g.player.carrying("wood") > 0
                                   and not g.tile().terrain.drinkable)),
           prompt=_fire_prompt),
    Action(REST, "rest", _rest,
           prompt=lambda g: "Sit and rest"),
    Action(SLEEP, "sleep", _sleep,
           prompt=_sleep_prompt),
    Action(STILL, "be still", _be_still,
           conceivable=_stillness_still_occurs,
           prompt=lambda g: "Be still"),
)

BY_KEY = {action.key: action for action in ACTIONS}


def conceivable(game) -> list[Action]:
    """The actions that currently occur to the character at all.

    This is the Soul narrowing, and it is decided here in the simulation. The
    interface asks; it never decides for itself what to hide.
    """
    return [a for a in ACTIONS if a.conceivable(game)]


def available(game) -> list[Action]:
    """Conceivable actions that are also worth offering where you stand."""
    return [a for a in conceivable(game) if a.relevant(game)]
