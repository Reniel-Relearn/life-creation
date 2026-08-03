"""The simulation.

Holds the world, the character and the clock, and advances them. This module
owns the rules and nothing else owns any of them. It imports no front end, no
graphics framework, and it never prints (DESIGN.md section 6, rule 1).

Every turn goes in as a Command and comes back as an Outcome. That is the only
way the rest of the program is allowed to talk to it.
"""

from __future__ import annotations

import random

from . import actions as actions_mod
from . import chronicle as chronicle_mod
from . import config, perception, player as player_mod, skills, world as world_mod
from .clock import Clock
from .commands import Command, CommandKind, Direction
from .fire import Hearths
from .outcomes import Event, EventKind, Outcome, refused


class Game:
    """One life, from waking to death."""

    def __init__(self, name: str, seed: int | None = None,
                 time_scale: float = 1.0):
        self.world, self.world_report = world_mod.new_world(seed)
        start_x, start_y = self.world.find_start()
        self.player = player_mod.wake(name, start_x, start_y)
        self.clock = Clock(scale=time_scale)
        self.chronicle = chronicle_mod.Chronicle()
        self.fires = Hearths()
        self.log: list[str] = []

        # One seeded stream for everything the simulation rolls for. Nothing in
        # the game touches the global `random` module.
        self.rng = random.Random(self.world.seed ^ 0xA11_11FE)

        self._was_night = self.clock.is_night
        self._pending: list[Event] = []
        self._visible: frozenset[tuple[int, int]] = frozenset()

        self.chronicle.discovered_terrain(self.tile().terrain.name)
        self.reveal()

    # -- convenience --------------------------------------------------------

    def tile(self, x: int | None = None, y: int | None = None):
        return self.world.at(
            self.player.x if x is None else x,
            self.player.y if y is None else y,
        )

    def say(self, message: str) -> None:
        if not message:
            return
        self.log.append(message)
        if len(self.log) > config.MAX_LOG_ENTRIES:
            del self.log[0]

    @property
    def seed(self) -> int:
        return self.world.seed

    @property
    def alive(self) -> bool:
        return self.player.alive

    # -- environment --------------------------------------------------------

    def sight_radius(self) -> int:
        return perception.sight_radius(self)

    def visible(self) -> frozenset[tuple[int, int]]:
        """Tiles the character can see right now. Recomputed on each turn."""
        return self._visible

    def effective_temperature(self, x: int | None = None,
                              y: int | None = None) -> float:
        px = self.player.x if x is None else x
        py = self.player.y if y is None else y
        temp = self.clock.ambient_temperature()
        temp += self.world.at(px, py).terrain.shelter
        temp += self.fires.warmth_at(px, py)
        return temp

    def reveal(self) -> None:
        """Mark what can be seen. Curiosity is what feeds the soul."""
        self._visible = perception.visible_tiles(self)
        gained = 0
        for x, y in self._visible:
            tile = self.world.at(x, y)
            if not tile.seen:
                tile.seen = True
                gained += 1
        if gained:
            self.player.tiles_seen += gained
            self.player.needs.soul += config.SOUL_PER_NEW_TILE * gained
            self.player.needs.clamp()

    # -- time ---------------------------------------------------------------

    def advance(self, minutes: float, resting: bool = False) -> None:
        """Advance the simulation in small chunks so nothing is skipped over."""
        remaining = float(self.clock.scaled(minutes))
        while remaining > 0 and self.player.alive:
            chunk = min(config.TICK_CHUNK_MINUTES, remaining)
            remaining -= chunk

            self.clock.advance(chunk)
            self._burn_fires(chunk)
            self.player.needs.tick(
                chunk, self.effective_temperature(), resting=resting)
            self._check_dawn()

        if not self.player.alive:
            self._die()

    def _burn_fires(self, minutes: float) -> None:
        for fire in self.fires.burn(minutes, self.clock.minutes):
            if (fire.x, fire.y) == (self.player.x, self.player.y):
                self._emit(EventKind.FIRE_DIED, fire.x, fire.y,
                           "The fire has burned down to nothing.")
            else:
                self._emit(EventKind.FIRE_DIED, fire.x, fire.y)
        self.fires.forget_dead()

    def _check_dawn(self) -> None:
        night_now = self.clock.is_night
        if self._was_night and not night_now:
            self.player.nights_survived += 1
            self.player.needs.soul += config.SOUL_PER_NIGHT_SURVIVED
            self.player.needs.clamp()
            self._emit(EventKind.NIGHT_SURVIVED, self.player.x, self.player.y,
                       "You came through the night.")
        self._was_night = night_now

    def _die(self) -> None:
        if self.chronicle.has("death"):
            return
        cause = self.player.needs.death_cause or "unknown"
        self.chronicle.mark("death", self.clock, f"you died of {cause}")
        self._emit(EventKind.DIED, self.player.x, self.player.y, "")

    # -- events -------------------------------------------------------------

    def _emit(self, kind: EventKind, x: int | None = None, y: int | None = None,
              text: str = "") -> None:
        self._pending.append(Event(kind, x, y, text))
        if text:
            self.say(text)

    def _drain(self) -> list[Event]:
        events, self._pending = self._pending, []
        return events

    # -- the only way in ----------------------------------------------------

    def submit(self, command: Command) -> Outcome:
        """Resolve one turn. This is the simulation's entire public surface."""
        if not self.player.alive:
            return refused(command.name, "You are dead.")
        if command.kind is CommandKind.MOVE:
            assert command.direction is not None
            return self._move(command.direction)
        assert command.action_key is not None
        return self._act(command.action_key)

    # -- movement -----------------------------------------------------------

    def _move(self, direction: Direction) -> Outcome:
        dx, dy = direction.delta
        from_x, from_y = self.player.x, self.player.y
        nx, ny = from_x + dx, from_y + dy

        if not self.world.in_bounds(nx, ny):
            message = "The world ends here."
            self.say(message)
            outcome = refused("move", message)
            outcome.from_x, outcome.from_y = from_x, from_y
            outcome.to_x, outcome.to_y = from_x, from_y
            outcome.events = [Event(EventKind.BLOCKED, from_x, from_y, message)]
            return outcome

        target = self.world.at(nx, ny)
        wading = target.terrain.drinkable and not target.terrain.still_water

        self.player.x, self.player.y = nx, ny
        self._apply_monotony("move")
        skills.practise(self.player.skills, skills.WANDERING)

        if not target.seen:
            self._emit(EventKind.DISCOVERED, nx, ny)
        self.chronicle.discovered_terrain(target.terrain.name)

        if wading:
            self.player.pay_rest(config.WADE_REST_COST)
            self.player.needs.warmth -= config.WADE_WARMTH_COST
            self.player.needs.clamp()
            self._emit(EventKind.WADED, nx, ny,
                       "You wade in. The cold of it goes straight through you.")
            minutes = config.WADE_MINUTES
        else:
            self.player.pay_rest(config.MOVE_REST_COST)
            self.player.needs.clamp()
            self._emit(EventKind.MOVED, nx, ny)
            minutes = config.MOVE_MINUTES

        self.advance(minutes)
        self.reveal()
        self.chronicle.record_action("move", minutes)

        return Outcome(
            ok=True,
            command_name="move",
            minutes=minutes,
            messages=[],
            events=self._drain(),
            from_x=from_x, from_y=from_y,
            to_x=self.player.x, to_y=self.player.y,
            alive=self.player.alive,
        )

    # -- actions ------------------------------------------------------------

    def _act(self, key: str) -> Outcome:
        action = actions_mod.BY_KEY.get(key)
        if action is None:
            return refused(key, "")
        if not action.conceivable(self):
            # It does not occur to the character. Nothing is announced, and the
            # game never says why.
            return refused(key, "")

        was_lit = self.fires.at(self.player.x, self.player.y) is not None
        result = action.perform(self)
        for message in result.messages:
            self.say(message)

        if not result.ok:
            outcome = refused(key, result.messages[0] if result.messages else "")
            outcome.from_x = outcome.to_x = self.player.x
            outcome.from_y = outcome.to_y = self.player.y
            return outcome

        if not was_lit and self.fires.at(self.player.x, self.player.y):
            self.chronicle.fire_made()

        self._pending.extend(result.events)
        self._apply_monotony(key)
        self.player.needs.clamp()
        self.advance(result.minutes, resting=result.resting)
        self.reveal()
        self.chronicle.record_action(key, result.minutes)

        return Outcome(
            ok=True,
            command_name=key,
            minutes=result.minutes,
            messages=result.messages,
            events=self._drain(),
            from_x=self.player.x, from_y=self.player.y,
            to_x=self.player.x, to_y=self.player.y,
            alive=self.player.alive,
        )

    def _apply_monotony(self, key: str) -> None:
        penalty = self.player.record_action(key)
        if penalty:
            self.player.needs.soul -= penalty
            self.player.needs.clamp()

    # -- the end ------------------------------------------------------------

    def ending(self) -> list[str]:
        return chronicle_mod.compose(
            self.player, self.clock, self.world, self.chronicle
        )
