"""The controller.

Sits between the screen and the simulation. It translates input into commands,
holds the input lock while the screen is busy animating a finished turn, and
starts and restarts runs. No survival rule lives here, and nothing here draws.
"""

from __future__ import annotations

import logging

from . import config, viewmodel
from .commands import Command, Direction
from .game import Game
from .outcomes import EventKind, Outcome

log = logging.getLogger(__name__)


class Session:
    """One run of the game, plus the turn gate that keeps it honest."""

    def __init__(self, name: str, seed: int | None = None,
                 time_scale: float = 1.0):
        self.name = name
        self.requested_seed = seed
        self.time_scale = time_scale
        self.game = Game(name, seed, time_scale=time_scale)
        self._animating = False
        self.turns = 0
        log.info("run started: name=%s seed=%s attempts=%s",
                 name, self.game.seed, self.game.world_report.attempts)

    # -- the input lock -----------------------------------------------------
    #
    # The simulation resolves a turn instantly. The screen then spends a little
    # while showing what happened. Input is refused for exactly that long, so a
    # player leaning on a key cannot bank a queue of accidental turns.

    @property
    def busy(self) -> bool:
        return self._animating

    @property
    def accepting_input(self) -> bool:
        return not self._animating and self.game.alive

    def animation_finished(self) -> None:
        self._animating = False

    # -- turns --------------------------------------------------------------

    def submit(self, command: Command) -> Outcome | None:
        """Resolve one turn, or return None if the turn was not allowed.

        None means "nothing happened, and no time passed" - the caller should
        not animate anything.
        """
        if not self.accepting_input:
            return None

        outcome = self.game.submit(command)
        if not outcome.ok:
            # A refused turn costs nothing and does not lock input. The player
            # walked into the edge of the world; that is not a turn.
            return outcome

        self.turns += 1
        self._animating = True
        return outcome

    def move(self, direction: Direction) -> Outcome | None:
        return self.submit(Command.move(direction))

    def act(self, key: str) -> Outcome | None:
        return self.submit(Command.action(key))

    # -- presentation timing ------------------------------------------------

    def animation_seconds(self, outcome: Outcome) -> float:
        """How long the screen should spend presenting this turn.

        Presentation only. Nothing here feeds back into the simulation - the
        turn has already been resolved by the time this is asked.
        """
        if outcome.has(EventKind.WADED):
            return config.WADE_ANIM_SECONDS
        if outcome.has(EventKind.SLEPT):
            return config.SLEEP_ANIM_SECONDS
        if outcome.command_name == "move":
            return config.MOVE_ANIM_SECONDS
        return config.ACTION_ANIM_SECONDS

    # -- readings -----------------------------------------------------------

    def view(self) -> viewmodel.PlayView:
        return viewmodel.build(self.game)

    def ending(self) -> list[str]:
        return self.game.ending()

    @property
    def seed(self) -> int:
        return self.game.seed

    # -- lifecycle ----------------------------------------------------------

    def restart(self, name: str | None = None,
                seed: int | None = None) -> "Session":
        """Begin a new life. One run is one life; nothing carries over."""
        return Session(
            name if name is not None else self.name,
            seed,
            time_scale=self.time_scale,
        )
