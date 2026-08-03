"""The world: a flat square grid of terrain, procedurally generated.

Bounded and finite by design (DESIGN.md section 9). Resources are finite per
tile and do not regrow in the MVP, which is what forces the player to move.

Generation is deterministic: the same seed always produces the same world. The
world owns its own random number generator and never touches the global one.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from . import config


class TerrainType(str, Enum):
    GRASS = "grass"
    FOREST = "forest"
    WATER = "water"
    HILLS = "hills"
    MARSH = "marsh"
    BARE = "bare"


@dataclass(frozen=True)
class Terrain:
    key: TerrainType
    name: str
    char: str            # terminal front end
    colour: int          # terminal front end: xterm-256 colour index
    rgb: tuple[int, int, int]   # graphical front end
    shelter: float       # degrees added to (or taken from) ambient temperature
    drinkable: bool = False
    still_water: bool = False


TERRAIN: dict[TerrainType, Terrain] = {
    TerrainType.GRASS: Terrain(
        TerrainType.GRASS, "grassland", '"', 107, (104, 138, 78), shelter=0.0),
    TerrainType.FOREST: Terrain(
        TerrainType.FOREST, "forest", "T", 28, (48, 88, 56), shelter=4.0),
    TerrainType.WATER: Terrain(
        TerrainType.WATER, "running water", "~", 39, (58, 110, 158),
        shelter=-2.0, drinkable=True),
    TerrainType.HILLS: Terrain(
        TerrainType.HILLS, "rocky hills", "^", 245, (128, 122, 112),
        shelter=-3.0),
    TerrainType.MARSH: Terrain(
        TerrainType.MARSH, "marsh", ",", 100, (108, 116, 82), shelter=-1.0,
        drinkable=True, still_water=True),
    TerrainType.BARE: Terrain(
        TerrainType.BARE, "bare earth", ".", 240, (122, 106, 88), shelter=-1.0),
}


@dataclass
class Tile:
    terrain: Terrain
    resources: dict[str, int] = field(default_factory=dict)
    seen: bool = False
    # A stable per-tile value in 0..1, fixed at generation. The renderer uses it
    # for texture variation so the same world always looks the same.
    variant: float = 0.0

    def take(self, key: str, amount: int = 1) -> int:
        """Remove up to `amount` of a resource. Returns how much was taken."""
        available = self.resources.get(key, 0)
        taken = min(available, amount)
        if taken:
            self.resources[key] = available - taken
        return taken


@dataclass
class WorldReport:
    """What generation validation found. Empty `problems` means usable."""
    seed: int
    attempts: int = 1
    terrain_counts: dict[str, int] = field(default_factory=dict)
    water_distance: int = -1
    wood_distance: int = -1
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


class World:
    def __init__(self, width: int, height: int, seed: int | None = None):
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randrange(1, 2**31)
        # Generation and spawn draw from separate streams, so a change to one
        # cannot silently shift the other.
        self._rng = random.Random(self.seed)
        self._spawn_rng = random.Random(self.seed ^ 0x5EED_5A17)
        self.tiles: list[list[Tile]] = []
        self._generate(self._rng)

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

    def adjacent_to_terrain(self, x: int, y: int, key: TerrainType) -> bool:
        if self.at(x, y).terrain.key == key:
            return True
        return any(t.terrain.key == key for _, _, t in self.neighbours(x, y))

    def terrain_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self.tiles:
            for tile in row:
                key = tile.terrain.key.value
                counts[key] = counts.get(key, 0) + 1
        return counts

    # -- generation ---------------------------------------------------------

    def _generate(self, rng: random.Random) -> None:
        grid = [[TerrainType.GRASS] * self.width for _ in range(self.height)]

        self._carve_river(grid, rng)
        self._scatter(grid, rng, TerrainType.FOREST,
                      config.FOREST_CLUMPS, config.FOREST_SIZE)
        self._scatter(grid, rng, TerrainType.HILLS,
                      config.HILLS_CLUMPS, config.HILLS_SIZE)
        self._scatter(grid, rng, TerrainType.BARE,
                      config.BARE_CLUMPS, config.BARE_SIZE)
        self._edge_marsh(grid, rng)

        self.tiles = [
            [self._make_tile(grid[y][x], rng) for x in range(self.width)]
            for y in range(self.height)
        ]

    def _carve_river(self, grid, rng: random.Random) -> None:
        x = rng.randrange(self.width // 4, self.width * 3 // 4)
        for y in range(self.height):
            width = rng.choice(config.RIVER_WIDTH_CHOICES)
            for w in range(width):
                if 0 <= x + w < self.width:
                    grid[y][x + w] = TerrainType.WATER
            x += rng.choice(config.RIVER_DRIFT_CHOICES)
            x = max(1, min(self.width - 3, x))

    def _scatter(self, grid, rng: random.Random, key: TerrainType,
                 clumps: int, size: int) -> None:
        for _ in range(clumps):
            cx = rng.randrange(self.width)
            cy = rng.randrange(self.height)
            frontier = [(cx, cy)]
            placed = 0
            while frontier and placed < size:
                x, y = frontier.pop(rng.randrange(len(frontier)))
                if not self.in_bounds(x, y) or grid[y][x] == TerrainType.WATER:
                    continue
                if grid[y][x] == key:
                    continue
                grid[y][x] = key
                placed += 1
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    if rng.random() < config.SCATTER_SPREAD_CHANCE:
                        frontier.append((x + dx, y + dy))

    def _edge_marsh(self, grid, rng: random.Random) -> None:
        for y in range(self.height):
            for x in range(self.width):
                if grid[y][x] != TerrainType.GRASS:
                    continue
                touching_water = any(
                    self.in_bounds(x + dx, y + dy)
                    and grid[y + dy][x + dx] == TerrainType.WATER
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
                )
                if touching_water and rng.random() < config.MARSH_CHANCE_BESIDE_WATER:
                    grid[y][x] = TerrainType.MARSH

    def _make_tile(self, key: TerrainType, rng: random.Random) -> Tile:
        resources: dict[str, int] = {}
        if key == TerrainType.GRASS:
            resources["forage"] = rng.randint(*config.GRASS_FORAGE_RANGE)
        elif key == TerrainType.FOREST:
            resources["forage"] = rng.randint(*config.FOREST_FORAGE_RANGE)
            resources["wood"] = rng.randint(*config.FOREST_WOOD_RANGE)
        elif key == TerrainType.HILLS:
            resources["stone"] = rng.randint(*config.HILLS_STONE_RANGE)
            if rng.random() < config.HILLS_FLINT_CHANCE:
                resources["flint"] = rng.randint(*config.HILLS_FLINT_RANGE)
        elif key == TerrainType.MARSH:
            resources["forage"] = rng.randint(*config.MARSH_FORAGE_RANGE)
            resources["reeds"] = rng.randint(*config.MARSH_REED_RANGE)
        return Tile(terrain=TERRAIN[key], resources=resources,
                    variant=rng.random())

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
            if self.tiles[y][x].terrain.key in (TerrainType.GRASS,
                                                TerrainType.FOREST)
        ]
        self._spawn_rng.shuffle(candidates)
        for x, y in candidates:
            if (self.distance_to_water(x, y) <= config.SPAWN_WATER_WITHIN
                    and self.distance_to_resource(x, y, "wood")
                    <= config.SPAWN_WOOD_WITHIN):
                return x, y
        for x, y in candidates:
            if self.distance_to_water(x, y) <= config.SPAWN_FALLBACK_WATER_WITHIN:
                return x, y
        return candidates[0] if candidates else (self.width // 2, self.height // 2)

    # -- measurement --------------------------------------------------------

    def distance_to_resource(self, x: int, y: int, key: str,
                             limit: int = config.SPAWN_SEARCH_LIMIT) -> int:
        """Chebyshev distance to the nearest tile holding `key`, or limit + 1."""
        return self._nearest(
            x, y, limit, lambda t: t.resources.get(key, 0) > 0)

    def distance_to_water(self, x: int, y: int,
                          limit: int = config.SPAWN_SEARCH_LIMIT) -> int:
        return self._nearest(x, y, limit, lambda t: t.terrain.drinkable)

    def _nearest(self, x: int, y: int, limit: int, wanted) -> int:
        for radius in range(limit + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue
                    nx, ny = x + dx, y + dy
                    if self.in_bounds(nx, ny) and wanted(self.tiles[ny][nx]):
                        return radius
        return limit + 1

    def reachable_from(self, x: int, y: int, wanted) -> bool:
        """Breadth-first search over the whole grid.

        Every terrain in this slice is passable - running water is waded, not
        blocked - so this is a genuine reachability check rather than a
        formality only once impassable terrain exists.
        """
        from collections import deque

        if not self.in_bounds(x, y):
            return False
        if wanted(self.at(x, y)):
            return True
        seen = {(x, y)}
        queue = deque([(x, y)])
        while queue:
            cx, cy = queue.popleft()
            for nx, ny, tile in self.neighbours(cx, cy):
                if (nx, ny) in seen:
                    continue
                seen.add((nx, ny))
                if wanted(tile):
                    return True
                queue.append((nx, ny))
        return False

    # -- validation ---------------------------------------------------------

    def validate(self, start: tuple[int, int] | None = None) -> WorldReport:
        """Reject structurally broken worlds, not merely difficult ones."""
        if start is None:
            start = self.find_start()
        sx, sy = start

        counts = self.terrain_counts()
        report = WorldReport(seed=self.seed, terrain_counts=counts)
        problems = report.problems

        if len(counts) < config.WORLD_MIN_TERRAIN_TYPES:
            problems.append(
                f"only {len(counts)} terrain types "
                f"(need {config.WORLD_MIN_TERRAIN_TYPES})")

        water_tiles = counts.get(TerrainType.WATER.value, 0)
        if water_tiles < config.WORLD_MIN_WATER_TILES:
            problems.append(f"only {water_tiles} water tiles")

        forest_tiles = counts.get(TerrainType.FOREST.value, 0)
        if forest_tiles < config.WORLD_MIN_FOREST_TILES:
            problems.append(f"only {forest_tiles} forest tiles")

        if not self.in_bounds(sx, sy):
            problems.append(f"spawn ({sx},{sy}) is out of bounds")
            return report

        if not self.reachable_from(sx, sy, lambda t: t.terrain.drinkable):
            problems.append("no reachable water")
        if not self.reachable_from(sx, sy, lambda t: t.resources.get("wood", 0) > 0):
            problems.append("no reachable deadwood")

        # Enclosure: with no impassable terrain this cannot happen, but the
        # check is here so it fails loudly the day impassable terrain arrives.
        if not any(True for _ in self.neighbours(sx, sy)):
            problems.append("spawn is enclosed")

        report.water_distance = self.distance_to_water(
            sx, sy, config.WORLD_VALIDATE_WATER_WITHIN)
        report.wood_distance = self.distance_to_resource(
            sx, sy, "wood", config.WORLD_VALIDATE_WOOD_WITHIN)

        if report.water_distance > config.WORLD_VALIDATE_WATER_WITHIN:
            problems.append("no water within reach of the first day")
        if report.wood_distance > config.WORLD_VALIDATE_WOOD_WITHIN:
            problems.append("no deadwood within reach of the first day")

        return report


def new_world(seed: int | None = None) -> tuple[World, WorldReport]:
    """Generate a validated world.

    A world that fails validation is broken, not hard. Broken worlds are
    regenerated from a derived seed rather than quietly patched, so meaningful
    variation - including punishing variation - survives.
    """
    base = seed if seed is not None else random.randrange(1, 2**31)
    last: tuple[World, WorldReport] | None = None

    for attempt in range(config.WORLD_MAX_GENERATION_ATTEMPTS):
        candidate_seed = base if attempt == 0 else (base + attempt * 7919) % (2**31)
        world = World(config.MAP_WIDTH, config.MAP_HEIGHT, candidate_seed)
        report = world.validate()
        report.attempts = attempt + 1
        if report.ok:
            return world, report
        last = (world, report)

    assert last is not None
    return last
