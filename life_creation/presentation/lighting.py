"""Day, dusk, night, and the light a fire throws.

Three layers, not one black rectangle:

    1. the per-tile fog tint, which the tile renderer owns
    2. an ambient wash that eases between the phases of the day
    3. additive lights around the character and every lit fire

The clock decides which phase it is. This module only decides how long the
colour takes to get there, and nothing here advances game time.
"""

from __future__ import annotations

import arcade

from .. import config
from ..clock import Phase
from . import space
from .assets import Assets


def _target(phase: Phase) -> tuple[float, float, float, float]:
    return tuple(float(c) for c in config.AMBIENT_TINT[phase.value])  # type: ignore[return-value]


class Lighting:
    def __init__(self, assets: Assets, world_height: int, phase: Phase):
        self.assets = assets
        self.world_height = world_height
        self.current = list(_target(phase))
        self.lights = arcade.SpriteList()
        self._pool: list[arcade.Sprite] = []

    def update(self, phase: Phase, delta_time: float) -> None:
        goal = _target(phase)
        t = min(1.0, config.LIGHT_TRANSITION_SPEED * delta_time)
        for i in range(4):
            self.current[i] = space.lerp(self.current[i], goal[i], t)

    @property
    def darkness(self) -> float:
        """0..1. How dark it currently is - the HUD dims with it."""
        return self.current[3] / 255.0

    # -- lights -------------------------------------------------------------

    def _borrow(self, index: int, texture) -> arcade.Sprite:
        while len(self._pool) <= index:
            sprite = arcade.Sprite(texture)
            self._pool.append(sprite)
            self.lights.append(sprite)
        sprite = self._pool[index]
        sprite.texture = texture
        sprite.visible = True
        return sprite

    def place(self, player_pos: tuple[float, float], fires,
              player_light: float) -> None:
        """Rebuild the light list from what the simulation says is burning."""
        index = 0

        for fire in fires:
            cx, cy = space.tile_centre(fire.x, fire.y, self.world_height)
            sprite = self._borrow(index, self.assets.fire_light)
            sprite.position = (cx, cy)
            reach = (fire.light_radius * 2 + 1) * config.TILE_SIZE
            sprite.width = sprite.height = reach
            sprite.alpha = int(180 + 60 * fire.strength)
            index += 1

        # The character carries a little light of their own, so the tile they
        # stand on is never pitch black. In daylight it does nothing at all.
        sprite = self._borrow(index, self.assets.light)
        sprite.position = player_pos
        sprite.width = sprite.height = player_light
        sprite.alpha = int(20 + 130 * self.darkness)
        index += 1

        for spare in self._pool[index:]:
            spare.visible = False

    # -- drawing ------------------------------------------------------------

    def draw(self, bounds: tuple[float, float, float, float]) -> None:
        left, right, bottom, top = bounds
        colour = tuple(int(c) for c in self.current)
        if colour[3] > 0:
            arcade.draw_lbwh_rectangle_filled(
                left, bottom, right - left, top - bottom, colour)

        ctx = arcade.get_window().ctx
        ctx.blend_func = ctx.BLEND_ADDITIVE
        self.lights.draw()
        ctx.blend_func = ctx.BLEND_DEFAULT
