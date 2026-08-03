"""A name, and a seed if you want one.

The game asks for nothing else. There is no character creation (DESIGN.md
section 10) - the character is made by what you do, not by what you pick here.
"""

from __future__ import annotations

import arcade

from .base import BACKDROP, DIM, FAINT, FONT, INK

NAME_FIELD = 0
SEED_FIELD = 1
MAX_NAME = 18
MAX_SEED = 10

_ALLOWED_NAME = set("abcdefghijklmnopqrstuvwxyz -'")
_ALLOWED_SEED = set("0123456789")


class NamingView(arcade.View):
    def __init__(self, app, default_seed: int | None = None):
        super().__init__()
        self.app = app
        self.name = ""
        self.seed = "" if default_seed is None else str(default_seed)
        self.field = NAME_FIELD
        self.caret = 0.0
        self._texts: dict[str, arcade.Text] = {}

    def on_show_view(self) -> None:
        self.window.background_color = BACKDROP
        w, h = self.window.width, self.window.height
        make = arcade.Text
        self._texts = {
            "prompt": make("What is your name?", w // 2, h * 0.62, INK, 20,
                           font_name=FONT, anchor_x="center"),
            "name": make("", w // 2, h * 0.52, INK, 22, font_name=FONT,
                         anchor_x="center", bold=True),
            "seed_label": make("seed (optional - the same seed is the same world)",
                               w // 2, h * 0.38, FAINT, 11, font_name=FONT,
                               anchor_x="center"),
            "seed": make("", w // 2, h * 0.32, DIM, 15, font_name=FONT,
                         anchor_x="center"),
            "footer": make("Tab  switch field      Enter  begin      Esc  back",
                           w // 2, h * 0.14, FAINT, 12, font_name=FONT,
                           anchor_x="center"),
        }

    def on_update(self, delta_time: float) -> None:
        self.caret = (self.caret + delta_time) % 1.0
        blink = "_" if self.caret < 0.55 else " "
        self._texts["name"].text = self.name + (blink if self.field == NAME_FIELD else "")
        self._texts["name"].color = INK if self.field == NAME_FIELD else DIM
        seed_text = self.seed or ("" if self.field == SEED_FIELD else "any")
        self._texts["seed"].text = seed_text + (blink if self.field == SEED_FIELD else "")
        self._texts["seed"].color = INK if self.field == SEED_FIELD else FAINT

    def on_draw(self) -> None:
        self.clear()
        self.window.default_camera.use()
        for text in self._texts.values():
            text.draw()

    # -- text entry ---------------------------------------------------------
    #
    # Driven from key symbols rather than the text event, so the same code path
    # can be exercised by the smoke test without a real keyboard.

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self.app.show_opening()
            return
        if symbol == arcade.key.TAB:
            self.field = SEED_FIELD if self.field == NAME_FIELD else NAME_FIELD
            return
        if symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self.begin()
            return
        if symbol == arcade.key.BACKSPACE:
            if self.field == NAME_FIELD:
                self.name = self.name[:-1]
            else:
                self.seed = self.seed[:-1]
            return

        self.type_character(symbol, modifiers)

    def type_character(self, symbol: int, modifiers: int = 0) -> None:
        if not (0 < symbol < 0x110000):
            return
        char = chr(symbol)
        if self.field == NAME_FIELD:
            if char not in _ALLOWED_NAME or len(self.name) >= MAX_NAME:
                return
            shifted = bool(modifiers & arcade.key.MOD_SHIFT)
            if not self.name or self.name.endswith(" "):
                char = char.upper()          # names read better capitalised
            elif shifted:
                char = char.upper()
            self.name += char
        else:
            if char in _ALLOWED_SEED and len(self.seed) < MAX_SEED:
                self.seed += char

    def begin(self) -> None:
        name = self.name.strip() or "Someone"
        seed = int(self.seed) if self.seed.strip() else None
        self.app.begin_run(name, seed)
