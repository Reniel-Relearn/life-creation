"""What the player can ask the simulation to do.

The presentation layer builds these from key presses and hands them to the
controller. It never calls into the simulation directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    @property
    def delta(self) -> tuple[int, int]:
        return _DELTAS[self]


_DELTAS = {
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
    Direction.RIGHT: (1, 0),
}


class CommandKind(str, Enum):
    MOVE = "move"
    ACTION = "action"


@dataclass(frozen=True)
class Command:
    kind: CommandKind
    direction: Direction | None = None
    action_key: str | None = None

    @staticmethod
    def move(direction: Direction) -> "Command":
        return Command(kind=CommandKind.MOVE, direction=direction)

    @staticmethod
    def action(key: str) -> "Command":
        return Command(kind=CommandKind.ACTION, action_key=key)

    @property
    def name(self) -> str:
        if self.kind is CommandKind.MOVE:
            return "move"
        return self.action_key or "?"
