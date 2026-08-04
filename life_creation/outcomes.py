"""What the simulation says happened.

An Outcome is the whole of what the presentation layer learns from a resolved
turn. The graphical layer animates these; it does not inspect the simulation to
work out what to draw.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EventKind(str, Enum):
    MOVED = "moved"
    WADED = "waded"
    BLOCKED = "blocked"
    DISCOVERED = "discovered"
    DRANK = "drank"
    FORAGED = "foraged"
    GATHERED = "gathered"
    FIRE_LIT = "fire_lit"
    FIRE_FAILED = "fire_failed"
    FIRE_FED = "fire_fed"
    FIRE_DIED = "fire_died"
    RESTED = "rested"
    SLEPT = "slept"
    STILLED = "stilled"
    NIGHT_SURVIVED = "night_survived"
    REFUSED = "refused"
    DIED = "died"


@dataclass(frozen=True)
class Event:
    """One thing that happened, at a place, that the screen may react to."""
    kind: EventKind
    x: int | None = None
    y: int | None = None
    text: str = ""


@dataclass
class ActionResult:
    """What an individual action reports back to the game."""
    minutes: int = 0
    messages: list[str] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    ok: bool = True
    resting: bool = False


@dataclass
class Outcome:
    """One resolved turn."""
    ok: bool
    command_name: str
    minutes: int = 0
    messages: list[str] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    from_x: int = 0
    from_y: int = 0
    to_x: int = 0
    to_y: int = 0
    alive: bool = True

    @property
    def moved(self) -> bool:
        return (self.from_x, self.from_y) != (self.to_x, self.to_y)

    def has(self, kind: EventKind) -> bool:
        return any(e.kind is kind for e in self.events)

    def first(self, kind: EventKind) -> Event | None:
        for event in self.events:
            if event.kind is kind:
                return event
        return None


def refused(command_name: str, message: str) -> Outcome:
    """A turn that did not happen. No time passes and nothing is recorded."""
    return Outcome(
        ok=False,
        command_name=command_name,
        messages=[message],
        events=[Event(EventKind.REFUSED, text=message)],
    )
