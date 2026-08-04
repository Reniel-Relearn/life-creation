"""The camera.

Follows the character, and stops at the edges of the world so the player never
sees past the end of it.
"""

from __future__ import annotations

import arcade

from .. import config
from . import space


class Follow:
    def __init__(self, window: arcade.Window, world_width: int,
                 world_height: int):
        self.camera = arcade.Camera2D()
        self.window = window
        self.world_pixels = space.world_pixel_size(world_width, world_height)
        self.x, self.y = 0.0, 0.0

    def snap_to(self, x: float, y: float) -> None:
        self.x, self.y = self._clamp(x, y)
        self.camera.position = (self.x, self.y)

    def follow(self, x: float, y: float, delta_time: float) -> None:
        target_x, target_y = self._clamp(x, y)
        # Frame-rate independent approach, so a slow machine does not lag behind.
        t = min(1.0, config.CAMERA_FOLLOW_SPEED * delta_time)
        self.x = space.lerp(self.x, target_x, t)
        self.y = space.lerp(self.y, target_y, t)
        self.camera.position = (self.x, self.y)

    def _clamp(self, x: float, y: float) -> tuple[float, float]:
        half_w = self.window.width / 2.0
        half_h = self.window.height / 2.0
        world_w, world_h = self.world_pixels

        if world_w <= self.window.width:
            cx = world_w / 2.0
        else:
            cx = max(half_w, min(world_w - half_w, x))
        if world_h <= self.window.height:
            cy = world_h / 2.0
        else:
            cy = max(half_h, min(world_h - half_h, y))
        return cx, cy

    def use(self) -> None:
        self.camera.use()

    @property
    def visible_bounds(self) -> tuple[float, float, float, float]:
        """left, right, bottom, top - in world pixels. For culling."""
        half_w = self.window.width / 2.0
        half_h = self.window.height / 2.0
        return (self.x - half_w, self.x + half_w,
                self.y - half_h, self.y + half_h)
