"""Terrain, drawn.

One sprite per tile, batched in a SpriteList and uploaded once. Fog of war is
applied as a per-sprite tint, and only the tiles whose state actually changed
are touched - so a turn costs a handful of writes, not a full rebuild.

This module renders what the simulation reports. It never decides what is
visible; it asks.
"""

from __future__ import annotations

import arcade

from .. import config
from ..world import TerrainType, World
from . import space
from .assets import Assets

UNSEEN = 0
REMEMBERED = 1
VISIBLE = 2


class TileRenderer:
    def __init__(self, world: World, assets: Assets):
        self.world = world
        self.assets = assets
        self.sprites = arcade.SpriteList()
        self._by_tile: dict[tuple[int, int], arcade.Sprite] = {}
        self._water: list[arcade.Sprite] = []
        self._state: dict[tuple[int, int], int] = {}
        self._water_frame = 0
        self._water_timer = 0.0
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
                self._state[(x, y)] = UNSEEN
                if tile.terrain.key is TerrainType.WATER:
                    self._water.append(sprite)

    # -- fog of war ---------------------------------------------------------

    def refresh(self, visible: frozenset[tuple[int, int]]) -> None:
        """Re-tint only the tiles whose visibility actually changed."""
        for (x, y), sprite in self._by_tile.items():
            if (x, y) in visible:
                wanted = VISIBLE
            elif self.world.at(x, y).seen:
                wanted = REMEMBERED
            else:
                wanted = UNSEEN

            if self._state[(x, y)] == wanted:
                continue
            self._state[(x, y)] = wanted
            self._apply(sprite, wanted)

    @staticmethod
    def _apply(sprite: arcade.Sprite, state: int) -> None:
        if state == VISIBLE:
            sprite.alpha = int(255 * config.FOG_VISIBLE)
            sprite.color = (255, 255, 255, sprite.alpha)
        elif state == REMEMBERED:
            # Recognisable, but subdued and drained of colour.
            level = int(255 * config.FOG_REMEMBERED)
            sprite.color = (level, level, int(level * 1.15), 255)
        else:
            sprite.alpha = int(255 * config.FOG_UNSEEN)

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
        self.sprites.draw()
