"""The first screen.

The question comes first and sits alone for a moment. The menu is allowed to
arrive afterwards, quietly, and it stays small.
"""

from __future__ import annotations

import arcade

from ... import config
from .base import BACKDROP, DIM, FAINT, FONT, INK

QUESTION_HOLD = 1.6      # seconds the question has the screen to itself
FADE_IN = 1.1
MENU_FADE = 0.9


class OpeningView(arcade.View):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.elapsed = 0.0
        self.question: arcade.Text | None = None
        self.subtitle: arcade.Text | None = None
        self.options: list[arcade.Text] = []

    def on_show_view(self) -> None:
        self.window.background_color = BACKDROP
        w, h = self.window.width, self.window.height
        self.question = arcade.Text(
            "How will you live your life?", w // 2, h * 0.60, (*INK, 0), 30,
            font_name=FONT, anchor_x="center", bold=True)
        self.subtitle = arcade.Text(
            "You wake with nothing. The world is already finished, "
            "and it is waiting.",
            w // 2, h * 0.52, (*DIM, 0), 13, font_name=FONT, anchor_x="center")
        labels = ("Enter    begin", "H    controls", "Esc    quit")
        self.options = [
            arcade.Text(label, w // 2, h * 0.30 - i * 26, (*FAINT, 0), 13,
                        font_name=FONT, anchor_x="center")
            for i, label in enumerate(labels)
        ]

    def on_update(self, delta_time: float) -> None:
        self.elapsed += delta_time

        alpha = min(1.0, self.elapsed / FADE_IN)
        if self.question:
            self.question.color = (*INK, int(255 * alpha))
        if self.subtitle:
            sub = max(0.0, min(1.0, (self.elapsed - FADE_IN * 0.6) / FADE_IN))
            self.subtitle.color = (*DIM, int(200 * sub))

        menu = max(0.0, min(1.0, (self.elapsed - QUESTION_HOLD - FADE_IN) / MENU_FADE))
        for option in self.options:
            option.color = (*FAINT, int(210 * menu))

    def on_draw(self) -> None:
        self.clear()
        self.window.default_camera.use()
        if self.question:
            self.question.draw()
        if self.subtitle:
            self.subtitle.draw()
        for option in self.options:
            option.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self.window.close()
        elif symbol == arcade.key.H:
            self.app.show_help(back_to=self)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN, arcade.key.SPACE):
            self.app.show_naming()


def opening_view(app) -> OpeningView:
    return OpeningView(app)


__all__ = ["OpeningView", "opening_view", "config"]
