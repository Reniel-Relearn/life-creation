"""The world: a flat square grid of terrain, procedurally generated.

Bounded and finite by design (DESIGN.md section 9). Resources are finite per
tile and do not regrow in the MVP, which is what forces the player to move.
"""

import random
from dataclasses import dataclass, field

from . import config


@dataclass(frozen=True)
class Terrain:
    key: str
    name: str
    char: str
    colour: int          # xterm-256 colour index
    shelter: float       # degrees added to (or taken from) ambient temperature
    drinkable: bool = False
    still_water: bool = False


TERRAIN = {
    "grass": Terrain("grass", "grassland", '"', 107, shelter=0.0),
    "forest": Terrain("forest", "forest", "T", 28, shelter=4.0),
    "water": Terrain("water", "running water", "~", 39, shelter=-2.0,
                     drinkable=True),
    "hills": Terrain("hills", "rocky hills", "^", 245, shelter=-3.0),
    "marsh": Terrain("marsh", "marsh", ",", 100, shelter=-1.0,
                     drinkable=True, still_water=True),
    "bare": Terrain("bare", "bare earth", ".", 240, shelter=-1.0),
}


@dataclass
class Tile:
    terrain: Terrain
    resources: dict = field(default_factory=dict)
    seen: bool = False
    fire_fuel: float = 0.0        # minutes of burn remaining

    @property
    def has_fire(self) -> bool:
        return self.fire_fuel > 0.0

    def take(self, key: str, amount: int = 1) -> int:
        """Remove up to `amount` of a resource. Returns how much was taken."""
        available = self.resources.get(key, 0)
        taken = min(available, amount)
        if taken:
            self.resources[key] = available - taken
        return taken


class World:
    def __init__(self, width: int, height: int, seed: int | None = None):
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randrange(1, 2**31)
        self._rng = random.Random(self.seed)
        self.tiles: list[list[Tile]] = []
        self._generate()

    # -- access -------------------------------------------------------------

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def at(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def neighbours(self, x: int, y: int):
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                yield nx, ny, self.tiles[ny][nx]

    def adjacent_to_terrain(self, x: int, y: int, key: str) -> bool:
        if self.at(x, y).terrain.key == key:
            return True
        return any(t.terrain.key == key for _, _, t in self.neighbours(x, y))

    # -- generation ---------------------------------------------------------

    def _generate(self) -> None:
        rng = self._rng
        grid = [["grass"] * self.width for _ in range(self.height)]

        self._carve_river(grid, rng)
        self._scatter(grid, rng, "forest", clumps=9, size=42)
        self._scatter(grid, rng, "hills", clumps=5, size=26)
        self._scatter(grid, rng, "bare", clumps=4, size=14)
        self._edge_marsh(grid, rng)

        self.tiles = [
            [self._make_tile(grid[y][x], rng) for x in range(self.width)]
            for y in range(self.height)
        ]

    def _carve_river(self, grid, rng) -> None:
        x = rng.randrange(self.width // 4, self.width * 3 // 4)
        for y in range(self.height):
            width = rng.choice((1, 1, 2))
            for w in range(width):
                if 0 <= x + w < self.width:
                    grid[y][x + w] = "water"
            x += rng.choice((-1, 0, 0, 0, 1))
            x = max(1, min(self.width - 3, x))

    def _scatter(self, grid, rng, key: str, clumps: int, size: int) -> None:
        for _ in range(clumps):
            cx = rng.randrange(self.width)
            cy = rng.randrange(self.height)
            frontier = [(cx, cy)]
            placed = 0
            while frontier and placed < size:
                x, y = frontier.pop(rng.randrange(len(frontier)))
                if not self.in_bounds(x, y) or grid[y][x] == "water":
                    continue
                if grid[y][x] == key:
                    continue
                grid[y][x] = key
                placed += 1
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    if rng.random() < 0.62:
                        frontier.append((x + dx, y + dy))

    def _edge_marsh(self, grid, rng) -> None:
        for y in range(self.height):
            for x in range(self.width):
                if grid[y][x] != "grass":
                    continue
                touching_water = any(
                    self.in_bounds(x + dx, y + dy) and grid[y + dy][x + dx] == "water"
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
                )
                if touching_water and rng.random() < 0.18:
                    grid[y][x] = "marsh"

    def _make_tile(self, key: str, rng) -> Tile:
        resources: dict[str, int] = {}
        if key == "grass":
            resources["forage"] = rng.randint(0, 3)
        elif key == "forest":
            resources["forage"] = rng.randint(1, 4)
            resources["wood"] = rng.randint(2, 6)
        elif key == "hills":
            resources["stone"] = rng.randint(1, 4)
            if rng.random() < 0.30:
                resources["flint"] = rng.randint(1, 2)
        elif key == "marsh":
            resources["forage"] = rng.randint(0, 2)
            resources["reeds"] = rng.randint(1, 3)
        return Tile(terrain=TERRAIN[key], resources=resources)

    # -- spawn --------------------------------------------------------------

    def find_start(self) -> tuple[int, int]:
        """Wake somewhere survivable.

        The game is meant to be hard, not a coin flip. You wake on open ground
        with water and deadwood both within a morning's walk. Everything after
        that is on the player.
        """
        candidates = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.tiles[y][x].terrain.key in ("grass", "forest")
        ]
        self._rng.shuffle(candidates)
        for x, y in candidates:
            if (self._distance_to_water(x, y) <= 6
                    and self._distance_to_resource(x, y, "wood") <= 5):
                return x, y
        for x, y in candidates:
            if self._distance_to_water(x, y) <= 8:
                return x, y
        return candidates[0] if candidates else (self.width // 2, self.height // 2)

    def _distance_to_resource(self, x: int, y: int, key: str,
                              limit: int = 8) -> int:
        for radius in range(limit + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = x + dx, y + dy
                    if (self.in_bounds(nx, ny)
                            and self.tiles[ny][nx].resources.get(key, 0) > 0):
                        return max(abs(dx), abs(dy))
        return limit + 1

    def _distance_to_water(self, x: int, y: int, limit: int = 8) -> int:
        for radius in range(limit + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = x + dx, y + dy
                    if self.in_bounds(nx, ny) and self.tiles[ny][nx].terrain.drinkable:
                        return max(abs(dx), abs(dy))
        return limit + 1


def new_world(seed: int | None = None) -> World:
    return World(config.MAP_WIDTH, config.MAP_HEIGHT, seed)
