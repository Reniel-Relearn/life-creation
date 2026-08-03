"""Tile coordinates to screen coordinates.

The simulation counts rows downward from the top of the map. OpenGL counts
upward from the bottom. This is the one place that difference is handled.
"""

from __future__ import annotations

from .. import config


def tile_centre(x: int, y: int, world_height: int) -> tuple[float, float]:
    size = config.TILE_SIZE
    return (
        x * size + size / 2.0,
        (world_height - 1 - y) * size + size / 2.0,
    )


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def world_pixel_size(width: int, height: int) -> tuple[float, float]:
    return width * config.TILE_SIZE, height * config.TILE_SIZE
