"""The character.

You wake with nothing. No backstory, no class, no stats to pick. Everything
below is either empty at the start or grows out of what you do.
"""

from dataclasses import dataclass, field

from . import config, skills
from .needs import Needs


@dataclass
class Player:
    name: str
    x: int
    y: int
    needs: Needs = field(default_factory=Needs)
    inventory: dict[str, int] = field(default_factory=dict)
    skills: dict[str, float] = field(default_factory=skills.blank)

    # Aging is a later phase (DESIGN.md section 3). The field exists now so the
    # data model does not have to change when it arrives.
    age_days: int = config.START_AGE_DAYS

    # bookkeeping the chronicle reads later
    tiles_seen: int = 0
    nights_survived: int = 0
    action_counts: dict[str, int] = field(default_factory=dict)
    last_action: str = ""
    repeat_streak: int = 0
    longest_repeat: int = 0

    @property
    def alive(self) -> bool:
        return self.needs.alive

    # -- inventory ----------------------------------------------------------

    def carrying(self, item: str) -> int:
        return self.inventory.get(item, 0)

    def add(self, item: str, amount: int = 1) -> None:
        if amount:
            self.inventory[item] = self.inventory.get(item, 0) + amount

    def spend(self, item: str, amount: int = 1) -> bool:
        if self.carrying(item) < amount:
            return False
        self.inventory[item] -= amount
        if self.inventory[item] <= 0:
            del self.inventory[item]
        return True

    # -- effort -------------------------------------------------------------

    def pay_rest(self, base_cost: float) -> None:
        """Work costs more when the body is empty."""
        self.needs.rest -= base_cost / self.needs.vigour

    # -- monotony -----------------------------------------------------------

    def record_action(self, key: str) -> float:
        """Track repetition. Returns the soul penalty this action earned."""
        self.action_counts[key] = self.action_counts.get(key, 0) + 1
        if key == self.last_action:
            self.repeat_streak += 1
        else:
            self.repeat_streak = 0
            self.last_action = key
        self.longest_repeat = max(self.longest_repeat, self.repeat_streak)

        beyond = self.repeat_streak - config.MONOTONY_THRESHOLD
        if beyond > 0:
            return config.MONOTONY_SOUL_PENALTY * beyond
        return 0.0

    def favourite_action(self) -> tuple[str, int]:
        if not self.action_counts:
            return ("", 0)
        key = max(self.action_counts, key=lambda k: self.action_counts[k])
        return key, self.action_counts[key]


def wake(name: str, x: int, y: int) -> Player:
    return Player(name=name, x=x, y=y)
