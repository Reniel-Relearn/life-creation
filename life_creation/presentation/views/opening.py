"""The first screen.

The question comes first and sits alone for a moment. The menu is allowed to
arrive afterwards, quietly, and it stays small.

A few embers drift up through the dark the whole time. They are the only warm
thing on the screen, which is the same thing they are in the game.
"""

from __future__ import annotations

import math
import random

import arcade

from .. import theme
from .base import FONT, key_menu

QUESTION_HOLD = 1.6      # seconds the question has the screen to itself
FADE_IN = 1.1
MENU_FADE = 0.9

EMBER_COUNT = 26

MENU = (
    ("Enter", "begin"),
    ("H", "controls"),
    ("Esc", "quit"),
)


class _Ember:
    """A slow warm mote. Decorative, cheap, and bounded to EMBER_COUNT."""

    __slots__ = ("x", "y", "speed", "drift", "phase", "size", "alpha")

    def __init__(self, rng: random.Random, width: int, height: int):
        self.reset(rng, width, height, anywhere=True)

    def reset(self, rng: random.Random, width: int, height: int,
              anywhere: bool = False) -> None:
        self.x = rng.uniform(0, width)
        self.y = rng.uniform(0, height) if anywhere else rng.uniform(-40, 0)
        self.speed = rng.uniform(8.0, 22.0)
        self.drift = rng.uniform(0.15, 0.5)
        self.phase = rng.uniform(0, math.tau)
        self.size = rng.uniform(1.4, 2.6)
        self.alpha = rng.uniform(0.10, 0.34)


class OpeningView(arcade.View):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.elapsed = 0.0
        self.question: arcade.Text | None = None
        self.subtitle: arcade.Text | None = None
        self.menu: list[arcade.Text] = []
        self._rng = random.Random(7)
        self._embers: list[_Ember] = []

    def on_show_view(self) -> None:
        self.window.background_color = theme.BACKDROP
        w, h = self.window.width, self.window.height

        self.question = arcade.Text(
            "How will you live your life?", w // 2, h * 0.58,
            theme.with_alpha(theme.INK, 0), theme.DISPLAY,
            font_name=FONT, anchor_x="center", bold=True)
        self.subtitle = arcade.Text(
            "You wake with nothing. The world is already finished, "
            "and it is waiting.",
            w // 2, h * 0.58 - theme.SPACE_6, theme.with_alpha(theme.MUTED, 0),
            theme.BODY, font_name=FONT, anchor_x="center")

        self.menu = key_menu(self.window, MENU, h * 0.26)
        for text in self.menu:
            text.color = theme.with_alpha(theme.SUBTLE, 0)

        self._embers = [_Ember(self._rng, w, h) for _ in range(EMBER_COUNT)]

    def on_update(self, delta_time: float) -> None:
        self.elapsed += delta_time
        w, h = self.window.width, self.window.height

        alpha = min(1.0, self.elapsed / FADE_IN)
        if self.question:
            self.question.color = theme.with_alpha(theme.INK, alpha)
        if self.subtitle:
            sub = max(0.0, min(1.0, (self.elapsed - FADE_IN * 0.6) / FADE_IN))
            self.subtitle.color = theme.with_alpha(theme.MUTED, 0.85 * sub)

        menu = max(0.0, min(1.0,
                            (self.elapsed - QUESTION_HOLD - FADE_IN) / MENU_FADE))
        for i, text in enumerate(self.menu):
            # Keys sit a shade brighter than their meanings.
            base = theme.MUTED if i % 2 == 0 else theme.SUBTLE
            text.color = theme.with_alpha(base, menu)

        for ember in self._embers:
            ember.y += ember.speed * delta_time
            ember.phase += delta_time * ember.drift
            if ember.y > h + 20:
                ember.reset(self._rng, w, h)

    def on_draw(self) -> None:
        self.clear()
        self.window.default_camera.use()

        for ember in self._embers:
            x = ember.x + math.sin(ember.phase) * 12.0
            arcade.draw_circle_filled(
                x, ember.y, ember.size, theme.with_alpha(theme.EMBER, ember.alpha))

        if self.question:
            self.question.draw()
        if self.subtitle:
            self.subtitle.draw()
        for text in self.menu:
            text.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self.window.close()
        elif symbol == arcade.key.H:
            self.app.show_help(back_to=self)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN, arcade.key.SPACE):
            self.app.show_naming()
