"""Terrain, drawn.

One sprite per tile, batched in a SpriteList and uploaded once. Fog of war is
applied as a per-sprite tint, and only the tiles whose state actually changed
are touched - so a turn costs a handful of writes, not a full rebuild.

This module renders what the simulation reports. It never decides what is
visible; it asks.
"""

from __future__ import annotations

import math

import arcade

from .. import config
from ..world import TerrainType, World
from . import space, theme
from .assets import Assets

# Sight does not stop at a wall. The last couple of tiles fade out, so the edge
# of vision reads as the edge of vision rather than as a rectangular hole cut
# in the world. Brightness is quantised so that only tiles whose step actually
# changed are re-tinted on a turn.
FALLOFF_TILES = 2.5
BRIGHTNESS_STEPS = 10


class TileRenderer:
    def __init__(self, world: World, assets: Assets):
        self.world = world
        self.assets = assets
        self.sprites = arcade.SpriteList()
        self._by_tile: dict[tuple[int, int], arcade.Sprite] = {}
        self._water: list[arcade.Sprite] = []
        self._level: dict[tuple[int, int], int] = {}
        self._water_frame = 0
        self._water_timer = 0.0
        self.world_pixels = space.world_pixel_size(world.width, world.height)
        self._build()

    def _build(self) -> None:
        for y in range(self.world.height):
            for x in range(self.world.width):
                tile = self.world.at(x, y)
                cx, cy = space.tile_centre(x, y, self.world.height)
                texture = self.assets.terrain_texture(tile.terrain.key,
                                                      tile.variant)
                sprite = arcade.Sprite(texture, center_x=cx, center_y=cy)
                sprite.alpha = 0
                self.sprites.append(sprite)
                self._by_tile[(x, y)] = sprite
                self._level[(x, y)] = -1
                if tile.terrain.key is TerrainType.WATER:
                    self._water.append(sprite)

    # -- fog of war ---------------------------------------------------------

    def refresh(self, visible: frozenset[tuple[int, int]],
                sources: list[tuple[int, int, int]]) -> None:
        """Re-tint the tiles whose brightness step changed.

        `sources` are the things that light the world - the character, and every
        lit fire - as (x, y, radius). The simulation decides what is visible;
        this only decides how softly the edge of it fades.
        """
        for (x, y), sprite in self._by_tile.items():
            seen = self.world.at(x, y).seen
            if (x, y) in visible:
                brightness = self._brightness(x, y, sources)
            else:
                brightness = 0.0

            if brightness > 0.0:
                level = 2 + int(brightness * BRIGHTNESS_STEPS)
            elif seen:
                level = 1
            else:
                level = 0

            if self._level[(x, y)] == level:
                continue
            self._level[(x, y)] = level
            self._apply(sprite, level, brightness)

    @staticmethod
    def _brightness(x: int, y: int, sources) -> float:
        """1.0 at the centre of sight, easing to 0 at its edge."""
        best = 0.0
        for sx, sy, radius in sources:
            distance = math.hypot(x - sx, y - sy)
            inner = max(0.0, radius - FALLOFF_TILES)
            if distance <= inner:
                return 1.0
            fade = 1.0 - (distance - inner) / FALLOFF_TILES
            best = max(best, fade)
        return max(0.0, min(1.0, best))

    @staticmethod
    def _apply(sprite: arcade.Sprite, level: int, brightness: float) -> None:
        if level == 0:                       # never seen
            sprite.alpha = 0
            return
        if level == 1:                       # remembered: subdued, cooled off
            tint = int(255 * config.FOG_REMEMBERED)
            sprite.color = (tint, tint, int(tint * 1.18), 255)
            return

        # In sight. Fade towards the remembered tone rather than to nothing, so
        # the edge of vision dissolves instead of ending.
        low = config.FOG_REMEMBERED
        value = low + (1.0 - low) * brightness
        tint = int(255 * value)
        cool = int(min(255, tint * (1.0 + 0.18 * (1.0 - brightness))))
        sprite.color = (tint, tint, cool, 255)

    # -- presentation only --------------------------------------------------

    def update_animation(self, delta_time: float) -> None:
        """Running water moves whether or not the game clock does."""
        if not self._water or not self.assets.water_frames:
            return
        self._water_timer += delta_time
        if self._water_timer < config.WATER_ANIM_SECONDS:
            return
        self._water_timer = 0.0
        self._water_frame = (self._water_frame + 1) % len(self.assets.water_frames)
        texture = self.assets.water_frames[self._water_frame]
        for sprite in self._water:
            sprite.texture = texture

    def draw(self) -> None:
        # A flat backing across the whole map first. Without it, unseen ground
        # is the window's own background and the world has no edge - which read
        # as an unfinished screen rather than as country you have not walked.
        # It is a single uniform colour, so it gives away nothing about what is
        # out there.
        width, height = self.world_pixels
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, theme.UNKNOWN_LAND)
        self.sprites.draw()
