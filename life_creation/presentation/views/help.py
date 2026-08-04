"""The controls.

Listed here and nowhere else. The world screen shows only what is worth doing
where you are standing, so this is the one place the full set is written down.
"""

from __future__ import annotations

import arcade

from .. import input as keys
from .. import theme
from .base import FONT, key_menu


class HelpView(arcade.View):
    def __init__(self, app, back_to: arcade.View):
        super().__init__()
        self.app = app
        self.back_to = back_to
        self._texts: list[arcade.Text] = []

    def on_show_view(self) -> None:
        self.window.background_color = theme.BACKDROP
        w, h = self.window.width, self.window.height
        top = h * 0.84

        self._texts = [
            arcade.Text("Controls", w // 2, top, theme.INK, theme.TITLE,
                        font_name=FONT, anchor_x="center")
        ]
        self._texts.extend(
            key_menu(self.window, keys.CONTROLS_HELP, top - theme.SPACE_6,
                     step=theme.SPACE_3))

        self._texts.append(arcade.Text(
            "Every action costs time. Time is the only thing you cannot get back.",
            w // 2, h * 0.12, theme.SUBTLE, theme.SMALL, font_name=FONT,
            anchor_x="center"))
        self._texts.append(arcade.Text(
            "Esc   back", w // 2, h * 0.06, theme.SUBTLE, theme.SMALL,
            font_name=FONT, anchor_x="center"))

    def on_draw(self) -> None:
        self.clear()
        self.window.default_camera.use()
        for text in self._texts:
            text.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol in (arcade.key.ESCAPE, arcade.key.H):
            self.window.show_view(self.back_to)
