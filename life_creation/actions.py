"""What you can do with a day.

Every action costs time, and most cost rest. Time is the real currency of the
game: a day spent gathering wood is a day not spent anywhere else.

Each `perform` takes the running game and returns an ActionResult. Actions never
print - they return messages for the log (DESIGN.md section 6, rule 1).
"""

import random
from dataclasses import dataclass, field
from typing import Callable

from . import config, skills


@dataclass
class ActionResult:
    minutes: int = 0
    messages: list[str] = field(default_factory=list)
    ok: bool = True
    resting: bool = False


@dataclass(frozen=True)
class Action:
    key: str
    label: str
    perform: Callable
    visible: Callable = lambda game: True


# ---------------------------------------------------------------------------
# Drink - water is the emergency. Three days, and it is over.
# ---------------------------------------------------------------------------

def _drink(game) -> ActionResult:
    tile = game.tile()
    source = None
    if tile.terrain.drinkable:
        source = tile.terrain
    else:
        for _, _, neighbour in game.world.neighbours(game.player.x, game.player.y):
            if neighbour.terrain.drinkable:
                source = neighbour.terrain
                break

    if source is None:
        return ActionResult(ok=False, messages=["There is no water within reach."])

    gain = config.DRINK_WATER_GAIN
    if source.still_water:
        gain *= config.MARSH_WATER_FACTOR
        note = "You drink from the marsh. It is flat and brackish."
    else:
        note = "You drink until your throat stops aching."

    game.player.needs.water += gain
    return ActionResult(minutes=config.DRINK_MINUTES, messages=[note])


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
    gain *= random.uniform(0.75, 1.25)
    player.needs.food += gain
    player.pay_rest(config.FORAGE_REST_COST)
    skills.practise(player.skills, skills.FORAGING)

    if gain > 11:
        msg = "You find roots and a good handful of berries."
    elif gain > 6:
        msg = "You turn up a few roots. Enough to matter."
    else:
        msg = "You scrape together something thin and bitter."
    return ActionResult(minutes=config.FORAGE_MINUTES, messages=[msg])


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
    return ActionResult(
        minutes=config.GATHER_MINUTES,
        messages=[f"You gather {got} wood. You are carrying {total}."],
    )


# ---------------------------------------------------------------------------
# Fire - the first real gate. Failing to light one as night falls is the game.
# ---------------------------------------------------------------------------

def _fire(game) -> ActionResult:
    player, tile = game.player, game.tile()

    if tile.has_fire:
        if not player.spend("wood", 1):
            return ActionResult(ok=False, messages=["You have no wood to feed it."])
        tile.fire_fuel = min(config.FIRE_MAX_FUEL,
                             tile.fire_fuel + config.FIRE_FUEL_PER_WOOD)
        return ActionResult(
            minutes=config.FEED_FIRE_MINUTES,
            messages=["You feed the fire. It takes the wood gratefully."],
        )

    if player.carrying("wood") < 1:
        return ActionResult(ok=False, messages=["You have no wood."])
    if player.needs.exhausted:
        return ActionResult(ok=False, messages=["Your hands are shaking too badly."])
    if tile.terrain.drinkable:
        return ActionResult(ok=False, messages=["Not here. The ground is wet."])

    level = skills.level(player.skills, skills.FIREMAKING)
    chance = config.FIREMAKING_BASE_CHANCE + config.FIREMAKING_SKILL_BONUS * level
    player.pay_rest(config.FIREMAKING_REST_COST)
    skills.practise(player.skills, skills.FIREMAKING)

    if random.random() < chance:
        player.spend("wood", 1)
        tile.fire_fuel = config.FIRE_FUEL_PER_WOOD
        game.fires.add((player.x, player.y))
        messages = ["The tinder catches. You have fire."]
        if not game.chronicle.has("first_fire"):
            game.chronicle.mark("first_fire", game.clock,
                                "you made fire for the first time")
            player.needs.soul += config.SOUL_PER_FIRST_FIRE
            messages.append("Something in you settles.")
        return ActionResult(minutes=config.FIREMAKING_MINUTES, messages=messages)

    return ActionResult(
        minutes=config.FIREMAKING_MINUTES,
        messages=["You work at it until your hands ache. Nothing catches."],
    )


# ---------------------------------------------------------------------------
# Rest and sleep
# ---------------------------------------------------------------------------

def _rest(game) -> ActionResult:
    game.player.needs.rest += config.REST_GAIN
    return ActionResult(
        minutes=config.REST_MINUTES,
        messages=["You sit a while and let your breath come back."],
        resting=True,
    )


def _sleep(game) -> ActionResult:
    clock = game.clock
    if clock.is_night:
        minutes = min(clock.minutes_until_hour(config.DAWN_HOUR),
                      config.SLEEP_MAX_HOURS * config.MINUTES_PER_HOUR)
    else:
        minutes = 6 * config.MINUTES_PER_HOUR

    game.player.needs.rest += config.SLEEP_GAIN_PER_MINUTE * minutes
    if game.tile().has_fire:
        opening = "You lie down by the fire."
    elif game.clock.is_night:
        opening = "You lie down in the dark."
    else:
        opening = "You lie down."
    return ActionResult(minutes=minutes, messages=[opening], resting=True)


# ---------------------------------------------------------------------------
# Be still - feeds Spirit. Costs time and returns nothing you can see.
# Disappears below a certain Soul, unannounced. Nothing explains this.
# ---------------------------------------------------------------------------

def _be_still(game) -> ActionResult:
    player = game.player
    player.needs.spirit += config.STILL_SPIRIT_GAIN
    skills.practise(player.skills, skills.STILLNESS)
    line = random.choice([
        "You stop, and do nothing, and let the time pass.",
        "You sit still until the noise in your head goes quiet.",
        "You are quiet for a while. Nothing comes of it.",
        "You rest without sleeping, and something in you loosens.",
    ])
    return ActionResult(minutes=config.STILL_MINUTES, messages=[line], resting=True)


def _stillness_still_occurs(game) -> bool:
    return game.player.needs.soul >= config.SOUL_STILLNESS_LOST_BELOW


# ---------------------------------------------------------------------------

ACTIONS: tuple[Action, ...] = (
    Action("d", "drink", _drink),
    Action("f", "forage", _forage),
    Action("g", "gather wood", _gather),
    Action("b", "build/feed fire", _fire),
    Action("r", "rest", _rest),
    Action("s", "sleep", _sleep),
    Action("m", "be still", _be_still, _stillness_still_occurs),
)

BY_KEY = {action.key: action for action in ACTIONS}


def available(game) -> list[Action]:
    """The actions that currently occur to the character."""
    return [a for a in ACTIONS if a.visible(game)]
