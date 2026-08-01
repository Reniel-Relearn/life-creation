"""The game loop.

Holds the world, the character and the clock, and advances the simulation. This
module owns the rules; `ui` owns the screen.
"""

from . import actions as actions_mod
from . import chronicle as chronicle_mod
from . import config, player as player_mod, skills, ui, world as world_mod
from .clock import Clock

DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


class Game:
    def __init__(self, name: str, seed: int | None = None):
        self.world = world_mod.new_world(seed)
        start_x, start_y = self.world.find_start()
        self.player = player_mod.wake(name, start_x, start_y)
        self.clock = Clock()
        self.chronicle = chronicle_mod.Chronicle()
        self.log: list[str] = []
        self.fires: set[tuple[int, int]] = set()
        self.running = True
        self._was_night = self.clock.is_night
        self.reveal()

    # -- convenience --------------------------------------------------------

    def tile(self, x: int | None = None, y: int | None = None):
        return self.world.at(
            self.player.x if x is None else x,
            self.player.y if y is None else y,
        )

    def say(self, message: str) -> None:
        if message:
            self.log.append(message)

    @property
    def seed(self) -> int:
        return self.world.seed

    # -- environment --------------------------------------------------------

    def sight_radius(self) -> int:
        radius = config.SIGHT_NIGHT if self.clock.is_night else config.SIGHT_DAY
        if self.tile().has_fire:
            radius += config.SIGHT_FIRE_BONUS
        return radius

    def effective_temperature(self) -> float:
        temp = self.clock.ambient_temperature()
        temp += self.tile().terrain.shelter
        if self.tile().has_fire:
            temp += config.FIRE_WARMTH_BONUS
        return temp

    def reveal(self) -> None:
        """Mark what can be seen. Curiosity is what feeds the soul."""
        radius = self.sight_radius()
        px, py = self.player.x, self.player.y
        gained = 0
        for y in range(py - radius, py + radius + 1):
            for x in range(px - radius, px + radius + 1):
                if not self.world.in_bounds(x, y):
                    continue
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
        remaining = float(minutes)
        while remaining > 0 and self.player.alive:
            chunk = min(config.TICK_CHUNK_MINUTES, remaining)
            remaining -= chunk

            self.clock.advance(chunk)
            self._burn_fires(chunk)
            self.player.needs.tick(chunk, self.effective_temperature(),
                                   resting=resting)
            self._check_dawn()

    def _burn_fires(self, minutes: float) -> None:
        for x, y in list(self.fires):
            tile = self.world.at(x, y)
            tile.fire_fuel -= minutes
            if tile.fire_fuel <= 0:
                tile.fire_fuel = 0.0
                self.fires.discard((x, y))
                if (x, y) == (self.player.x, self.player.y):
                    self.say("The fire has burned down to nothing.")

    def _check_dawn(self) -> None:
        night_now = self.clock.is_night
        if self._was_night and not night_now:
            self.player.nights_survived += 1
            self.player.needs.soul += config.SOUL_PER_NIGHT_SURVIVED
            self.say("You came through the night.")
        self._was_night = night_now

    # -- doing things -------------------------------------------------------

    def move(self, direction: str) -> None:
        dx, dy = DIRECTIONS[direction]
        nx, ny = self.player.x + dx, self.player.y + dy
        if not self.world.in_bounds(nx, ny):
            self.say("The world ends here.")
            return

        target = self.world.at(nx, ny)
        wading = target.terrain.key == "water"

        self.player.x, self.player.y = nx, ny
        penalty = self.player.record_action("move")
        self.player.needs.soul -= penalty
        skills.practise(self.player.skills, skills.WANDERING)

        if wading:
            self.player.pay_rest(config.WADE_REST_COST)
            self.player.needs.warmth -= config.WADE_WARMTH_COST
            self.player.needs.clamp()
            self.say("You wade in. The cold of it goes straight through you.")
            self.advance(config.WADE_MINUTES)
        else:
            self.player.pay_rest(config.MOVE_REST_COST)
            self.player.needs.clamp()
            self.advance(config.MOVE_MINUTES)

        self.reveal()

    def do_action(self, key: str) -> None:
        action = actions_mod.BY_KEY.get(key)
        if action is None or not action.visible(self):
            return

        result = action.perform(self)
        for message in result.messages:
            self.say(message)

        if not result.ok:
            return

        penalty = self.player.record_action(key)
        self.player.needs.soul -= penalty
        self.player.needs.clamp()
        self.advance(result.minutes, resting=result.resting)
        self.reveal()

    # -- the loop -----------------------------------------------------------

    def handle(self, key: str) -> None:
        if key == "q":
            self.running = False
        elif key in DIRECTIONS:
            self.move(key)
        elif key in ui.VI_KEYS:
            self.move(ui.VI_KEYS[key])
        else:
            self.do_action(key)

    def ending(self) -> list[str]:
        return chronicle_mod.compose(
            self.player, self.clock, self.world, self.chronicle
        )


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def play(seed: int | None = None) -> None:
    ui.setup_terminal()
    name = ui.title_screen()
    game = Game(name, seed)
    game.say("You wake with nothing.")

    ui.hide_cursor()
    try:
        while game.running and game.player.alive:
            ui.render(game)
            key = ui.read_key()
            game.handle(key)
    except KeyboardInterrupt:
        pass
    finally:
        ui.show_cursor()

    if not game.player.alive:
        ui.render(game)
    ui.ending_screen(game.ending())


def _step_toward(game, wanted) -> str | None:
    """Breadth-first search for the nearest tile satisfying `wanted`.

    Returns the direction of the first step, or None if already there or
    nothing was found. Used only by the demo autopilot.
    """
    from collections import deque

    start = (game.player.x, game.player.y)
    if wanted(game.world.at(*start)):
        return None

    came: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = deque([start])
    goal = None
    while queue and goal is None:
        x, y = queue.popleft()
        for nx, ny, tile in game.world.neighbours(x, y):
            if (nx, ny) in came:
                continue
            came[(nx, ny)] = (x, y)
            if wanted(tile):
                goal = (nx, ny)
                break
            queue.append((nx, ny))

    if goal is None:
        return None

    node = goal
    while came[node] != start:
        node = came[node]
    delta = (node[0] - start[0], node[1] - start[1])
    for name, offset in DIRECTIONS.items():
        if offset == delta:
            return name
    return None


def _autopilot_choice(game) -> str:
    """A crude survivor. Enough to prove the loop closes end to end."""
    player, needs, tile = game.player, game.player.needs, game.tile()

    # Spent bodies do nothing else until they have recovered.
    if needs.exhausted:
        return "s" if (game.clock.is_night and tile.has_fire) else "r"

    # Keep the fire alive above all else once it exists.
    if tile.has_fire and tile.fire_fuel < 240 and player.carrying("wood") > 0:
        return "b"

    # Night: get a fire lit and sleep by it.
    if game.clock.is_night or game.clock.hour >= config.DUSK_HOUR - 2:
        if not tile.has_fire and player.carrying("wood") > 0:
            return "b"
        if tile.has_fire and needs.rest < 70:
            return "s"

    # Cold is the fastest killer. Never idle through it.
    if needs.warmth < 40 and not tile.has_fire:
        if player.carrying("wood") > 0:
            return "b"
        step = _step_toward(game, lambda t: t.resources.get("wood", 0) > 0)
        return step or "g"

    if needs.water < 45:
        step = _step_toward(game, lambda t: t.terrain.drinkable)
        return step or "d"
    if needs.food < 45:
        step = _step_toward(game, lambda t: t.resources.get("forage", 0) > 0)
        return step or "f"
    if player.carrying("wood") < 8:
        step = _step_toward(game, lambda t: t.resources.get("wood", 0) > 0)
        return step or "g"
    if needs.rest < 35:
        return "r"
    return "m"


def demo(seed: int = 7, turns: int = 120) -> None:
    """Run the game under an autopilot, with no terminal input.

    This is the verification harness: it proves a full day/night cycle and a
    complete survival loop actually close.
    """
    ui.setup_terminal()
    game = Game("Adam", seed)
    game.say("You wake with nothing.")

    print(f"seed={game.seed}   start=({game.player.x},{game.player.y}) "
          f"in {game.tile().terrain.name}")
    print("-" * 88)
    print(f"{'do':<4}{'day':<5}{'time':<7}{'temp':>6}{'water':>7}{'food':>6}"
          f"{'warm':>6}{'rest':>6}{'hp':>5}{'soul':>6}{'spirit':>7}"
          f"{'wood':>6}  fire")
    print("-" * 88)

    last_day = game.clock.day
    for _ in range(turns):
        if not game.player.alive:
            break
        choice = _autopilot_choice(game)
        game.handle(choice)
        needs = game.player.needs
        print(
            f"{choice:<4}{game.clock.day:<5}{game.clock.clock_text():<7}"
            f"{game.effective_temperature():>6.1f}{needs.water:>7.1f}"
            f"{needs.food:>6.1f}{needs.warmth:>6.1f}{needs.rest:>6.1f}"
            f"{needs.health:>5.0f}{needs.soul:>6.1f}{needs.spirit:>7.2f}"
            f"{game.player.carrying('wood'):>6}"
            f"  {'lit' if game.tile().has_fire else '-'}"
        )
        if game.clock.day != last_day:
            last_day = game.clock.day
            print(f"{'':<4}--- day {last_day} ---")

    print("-" * 88)
    for line in game.log[-6:]:
        print("  > " + line)
    print()
    ui.render(game)
    ui.ending_screen(game.ending())
