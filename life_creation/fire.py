"""Fire.

The first real gate of the game (DESIGN.md section 8). Fire is a simulation
object with a position, fuel and a lifetime. The graphical layer draws flames
and light from what this says; it never decides any of it.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config


@dataclass
class Fire:
    x: int
    y: int
    fuel: float                 # minutes of burn remaining
    lit_at_minute: int          # absolute game minutes when it was first lit
    went_out_at_minute: int | None = None

    @property
    def lit(self) -> bool:
        return self.fuel > 0.0

    @property
    def warmth_radius(self) -> int:
        return config.FIRE_WARMTH_RADIUS

    @property
    def light_radius(self) -> int:
        return config.FIRE_LIGHT_RADIUS

    @property
    def strength(self) -> float:
        """0..1. How much fire there is - drives heat, light and flame size."""
        if self.fuel <= 0.0:
            return 0.0
        return min(1.0, self.fuel / config.FIRE_FUEL_PER_WOOD)

    def distance_to(self, x: int, y: int) -> int:
        return max(abs(self.x - x), abs(self.y - y))

    def warms(self, x: int, y: int) -> bool:
        return self.lit and self.distance_to(x, y) <= self.warmth_radius

    def lights(self, x: int, y: int) -> bool:
        return self.lit and self.distance_to(x, y) <= self.light_radius

    def feed(self, wood: int = 1) -> None:
        self.fuel = min(config.FIRE_MAX_FUEL,
                        self.fuel + config.FIRE_FUEL_PER_WOOD * wood)
        self.went_out_at_minute = None

    def burn(self, minutes: float, now: int) -> bool:
        """Burn for `minutes`. Returns True if the fire went out just now."""
        if not self.lit:
            return False
        self.fuel -= minutes
        if self.fuel <= 0.0:
            self.fuel = 0.0
            self.went_out_at_minute = now
            return True
        return False


class Hearths:
    """Every fire in the world, indexed by tile."""

    def __init__(self) -> None:
        self._fires: dict[tuple[int, int], Fire] = {}
        self.ever_lit = 0

    def __len__(self) -> int:
        return len(self._fires)

    def __iter__(self):
        return iter(self._fires.values())

    def at(self, x: int, y: int) -> Fire | None:
        fire = self._fires.get((x, y))
        return fire if fire is not None and fire.lit else None

    def light(self, x: int, y: int, now: int) -> Fire:
        fire = Fire(x=x, y=y, fuel=config.FIRE_FUEL_PER_WOOD, lit_at_minute=now)
        self._fires[(x, y)] = fire
        self.ever_lit += 1
        return fire

    def lit_fires(self) -> list[Fire]:
        return [f for f in self._fires.values() if f.lit]

    def warmth_at(self, x: int, y: int) -> float:
        """Degrees of heat reaching this tile, from the strongest fire near it."""
        best = 0.0
        for fire in self._fires.values():
            if not fire.warms(x, y):
                continue
            # Standing in it is the full bonus; a tile away is a share of it.
            falloff = 1.0 if fire.distance_to(x, y) == 0 else 0.55
            best = max(best, config.FIRE_WARMTH_BONUS * falloff * fire.strength)
        return best

    def light_bonus_at(self, x: int, y: int) -> int:
        """Extra tiles of sight granted by any fire close enough to help."""
        for fire in self._fires.values():
            if fire.lights(x, y):
                return config.SIGHT_FIRE_BONUS
        return 0

    def burn(self, minutes: float, now: int) -> list[Fire]:
        """Advance every fire. Returns the fires that went out during it."""
        died = []
        for fire in list(self._fires.values()):
            if fire.burn(minutes, now):
                died.append(fire)
        return died

    def forget_dead(self) -> None:
        """Drop burnt-out fires so the dictionary cannot grow without bound."""
        self._fires = {k: f for k, f in self._fires.items() if f.lit}
