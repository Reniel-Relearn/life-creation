"""The chronicle: what the game remembers, and what it says at the end.

There is no score. The game does not grade the life. It records what was
actually done and reads it back, in order, and stops.
"""

from dataclasses import dataclass, field

from . import config, skills


@dataclass
class Chronicle:
    marks: dict[str, tuple[int, str]] = field(default_factory=dict)

    def mark(self, key: str, clock, text: str) -> None:
        if key not in self.marks:
            self.marks[key] = (clock.day, text)

    def has(self, key: str) -> bool:
        return key in self.marks

    def day_of(self, key: str) -> int | None:
        entry = self.marks.get(key)
        return entry[0] if entry else None


_ACTION_PHRASES = {
    "f": "You spent most of your days looking for something to eat.",
    "g": "You spent most of your days carrying wood.",
    "d": "You spent most of your days going back to the water.",
    "b": "You spent most of your days tending a fire.",
    "r": "You spent most of your days sitting down.",
    "s": "You spent most of your days asleep.",
    "m": "You spent most of your days being still.",
    "move": "You spent most of your days walking.",
}

_DEATH_PHRASES = {
    "cold": "The cold took you.",
    "thirst": "You died of thirst.",
    "hunger": "You starved.",
}


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _fraction_seen(player, world) -> str:
    total = world.width * world.height
    if total <= 0:
        return "You saw nothing of the world."
    share = player.tiles_seen / total
    if share < 0.02:
        return "You never went far from where you woke."
    if share < 0.08:
        return "You kept to one corner of the world."
    if share < 0.25:
        return "You saw a little of the world."
    if share < 0.55:
        return "You saw a good deal of the world."
    return "You walked most of the world."


def compose(player, clock, world, chronicle: Chronicle) -> list[str]:
    """The account of a life. Plain declaratives, in order, then it stops."""
    lines: list[str] = []
    needs = player.needs

    days = clock.day
    day_word = "day" if days == 1 else "days"
    lines.append(f"{player.name} lived {days} {day_word}.")
    lines.append("")

    # How it ended.
    if not player.alive:
        lines.append(_DEATH_PHRASES.get(needs.death_cause, "You died."))
    else:
        lines.append("You were still alive when you set this down.")

    # What the days were spent on.
    key, count = player.favourite_action()
    if key and count > 2:
        lines.append(_ACTION_PHRASES.get(key, ""))

    best_skill, best_level = skills.best(player.skills)
    if best_level > 0.05:
        lines.append(
            f"By the end you were {skills.describe(best_level)} "
            f"at {skills.LABELS[best_skill]}."
        )
    else:
        lines.append("You never got good at anything.")

    # The world.
    lines.append(_fraction_seen(player, world))

    # Fire.
    fire_day = chronicle.day_of("first_fire")
    if fire_day:
        lines.append(f"You made fire on the {_ordinal(fire_day)} day.")
    else:
        lines.append("You never made fire.")

    # Nights.
    if player.nights_survived:
        nights = player.nights_survived
        night_word = "night" if nights == 1 else "nights"
        lines.append(f"You came through {nights} {night_word}.")

    lines.append("")

    # Soul - described, as it always was.
    if needs.soul >= 70:
        lines.append("You were still curious at the end.")
    elif needs.soul >= 40:
        lines.append("You had grown tired of it.")
    elif needs.soul >= 20:
        lines.append("The days had begun to blur, and then they stopped mattering.")
    else:
        lines.append("You had stopped noticing the days a long time before.")

    # Spirit - shown here, once, and nowhere else in the entire game.
    if needs.spirit >= config.START_SPIRIT + 8:
        lines.append(
            "You made time to be still. It cost you days you could not spare, "
            "and nothing came of it that anyone could see."
        )
    elif needs.spirit >= config.START_SPIRIT - 2:
        lines.append("You were still, now and then.")
    else:
        lines.append("You never once stopped.")

    lines.append("")
    lines.append("This is how you lived.")
    return lines
