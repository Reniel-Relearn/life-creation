"""The controls.

Listed here and nowhere else. The world screen shows only what is worth doing
where you are standing, so this is the one place the full set is written down.
"""

from __future__ import annotations

import arcade

from ... import config
from .. import input as keys
from .base import BACKDROP, DIM, FAINT, FONT, INK


class HelpView(arcade.View):
    def __init__(self, app, back_to: arcade.View):
        super().__init__()
        self.app = app
        self.back_to = back_to
        self._texts: list[arcade.Text] = []

    def on_show_view(self) -> None:
        self.window.background_color = BACKDROP
        w, h = self.window.width, self.window.height
        top = h * 0.80

        self._texts = [
            arcade.Text("Controls", w // 2, top, INK, 24, font_name=FONT,
                        anchor_x="center", bold=True)
        ]
        for i, (key, meaning) in enumerate(keys.CONTROLS_HELP):
            y = top - 60 - i * 26
            self._texts.append(arcade.Text(
                key, w * 0.36, y, INK, 13, font_name=FONT, anchor_x="right"))
            self._texts.append(arcade.Text(
                meaning, w * 0.40, y, DIM, 13, font_name=FONT))

        self._texts.append(arcade.Text(
            "Every action costs time. Time is the only thing you cannot get back.",
            w // 2, h * 0.16, FAINT, 12, font_name=FONT, anchor_x="center"))
        self._texts.append(arcade.Text(
            "Esc   back", w // 2, h * 0.09, FAINT, 12, font_name=FONT,
            anchor_x="center"))

    def on_draw(self) -> None:
        self.clear()
        self.window.default_camera.use()
        for text in self._texts:
            text.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol in (arcade.key.ESCAPE, arcade.key.H):
            self.window.show_view(self.back_to)


__all__ = ["HelpView", "config"]
