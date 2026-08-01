"""Skills grow by doing.

There is no experience menu and no character creation. Spend two hundred days
hunting and the character is a hunter. What you practised is who you were, and
the chronicle says so at the end.
"""

from . import config

FORAGING = "foraging"
WOODCRAFT = "woodcraft"
FIREMAKING = "firemaking"
WANDERING = "wandering"
STILLNESS = "stillness"

ALL = (FORAGING, WOODCRAFT, FIREMAKING, WANDERING, STILLNESS)

LABELS = {
    FORAGING: "foraging",
    WOODCRAFT: "woodcraft",
    FIREMAKING: "firemaking",
    WANDERING: "wandering",
    STILLNESS: "stillness",
}


def blank() -> dict[str, float]:
    return {name: 0.0 for name in ALL}


def practise(skills: dict[str, float], name: str,
             amount: float = config.SKILL_GAIN) -> None:
    """Doing a thing makes you better at it. Diminishing near mastery."""
    current = skills.get(name, 0.0)
    headroom = 1.0 - (current / config.SKILL_MAX)
    skills[name] = min(config.SKILL_MAX, current + amount * max(0.15, headroom))


def level(skills: dict[str, float], name: str) -> float:
    return skills.get(name, 0.0)


def describe(value: float) -> str:
    if value >= 0.85:
        return "masterful"
    if value >= 0.60:
        return "practised"
    if value >= 0.35:
        return "capable"
    if value >= 0.12:
        return "clumsy"
    return "untried"


def best(skills: dict[str, float]) -> tuple[str, float]:
    """The thing this life was mostly spent on."""
    name = max(ALL, key=lambda k: skills.get(k, 0.0))
    return name, skills.get(name, 0.0)
