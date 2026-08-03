"""Embers, and the small puffs an action leaves behind.

Bounded: the pool is allocated once and never grows past the cap in config.
Decorative only - no particle has ever affected a rule.
"""

from __future__ import annotations

import random

import arcade

from .. import config
from . import space


class Particles:
    def __init__(self, texture: arcade.Texture):
        self.sprites = arcade.SpriteList()
        self._texture = texture
        self._live: list[tuple[arcade.Sprite, list[float]]] = []
        self._free: list[arcade.Sprite] = []
        self._rng = random.Random(0)
        self._fire_timer = 0.0

    def _take(self) -> arcade.Sprite | None:
        if self._free:
            return self._free.pop()
        if len(self.sprites) >= config.MAX_PARTICLES:
            return None
        sprite = arcade.Sprite(self._texture)
        self.sprites.append(sprite)
        return sprite

    def emit(self, x: float, y: float, count: int = 1,
             rise: float = 26.0, spread: float = 14.0,
             lifetime: float = config.EMBER_LIFETIME,
             colour: tuple[int, int, int] = (255, 186, 96)) -> None:
        for _ in range(count):
            sprite = self._take()
            if sprite is None:
                return
            sprite.position = (x + self._rng.uniform(-6, 6),
                               y + self._rng.uniform(-4, 4))
            sprite.color = (*colour, 255)
            sprite.visible = True
            vx = self._rng.uniform(-spread, spread)
            vy = self._rng.uniform(rise * 0.5, rise)
            self._live.append((sprite, [vx, vy, lifetime, lifetime]))

    def fire_embers(self, fires, world_height: int, delta_time: float) -> None:
        self._fire_timer += delta_time
        if self._fire_timer < 0.18:
            return
        self._fire_timer = 0.0
        for fire in fires:
            cx, cy = space.tile_centre(fire.x, fire.y, world_height)
            self.emit(cx, cy + config.TILE_SIZE * 0.2,
                      count=config.EMBERS_PER_FIRE)

    def update(self, delta_time: float) -> None:
        still_live = []
        for sprite, state in self._live:
            state[2] -= delta_time
            if state[2] <= 0:
                sprite.visible = False
                self._free.append(sprite)
                continue
            sprite.center_x += state[0] * delta_time
            sprite.center_y += state[1] * delta_time
            state[1] *= 0.985
            sprite.alpha = int(255 * (state[2] / state[3]))
            still_live.append((sprite, state))
        self._live = still_live

    def draw(self) -> None:
        ctx = arcade.get_window().ctx
        ctx.blend_func = ctx.BLEND_ADDITIVE
        self.sprites.draw()
        ctx.blend_func = ctx.BLEND_DEFAULT
