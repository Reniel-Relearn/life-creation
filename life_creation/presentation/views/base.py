"""Shared furniture for the quiet screens.

The opening, the pause, the help and the chronicle are all the same shape: a
dark field, a little text, and nothing hurrying the player along.

Colour and type come from `theme.py`. The names below are kept as aliases so
every screen reads the same way, but the values are the audited ones - the old
`FAINT` grey failed contrast at 2.68:1 and was doing real work here.
"""

from __future__ import annotations

import arcade

from ... import config
from .. import theme

BACKDROP = theme.BACKDROP
INK = theme.INK
DIM = theme.MUTED
FAINT = theme.SUBTLE
FONT = config.TEXT_FONT


def key_menu(window, items: tuple[tuple[str, str], ...], top: float,
             colour=theme.SUBTLE, key_colour=theme.MUTED,
             size: int = theme.BODY,
             step: int = theme.SPACE_3) -> list[arcade.Text]:
    """A two-column key/meaning list, centred as a block.

    Centring each line on its own would rag the columns - which is exactly what
    the opening menu used to do. The gutter is the axis; keys are right-aligned
    into it and meanings left-aligned out of it.
    """
    axis = window.width // 2
    texts: list[arcade.Text] = []
    for i, (key, meaning) in enumerate(items):
        y = top - i * step
        texts.append(arcade.Text(key, axis - theme.SPACE_2, y, key_colour, size,
                                 font_name=FONT, anchor_x="right"))
        texts.append(arcade.Text(meaning, axis + theme.SPACE_2, y, colour, size,
                                 font_name=FONT))
    return texts


class Quiet(arcade.View):
    """A centred column of text on a dark field."""

    def __init__(self, title: str = "",
                 items: tuple[tuple[str, str], ...] = (),
                 footer: str = ""):
        super().__init__()
        self._title_text = title
        self._items = items
        self._footer_text = footer
        self._built = False
        self.title: arcade.Text | None = None
        self.lines: list[arcade.Text] = []
        self.footer: arcade.Text | None = None

    def build(self) -> None:
        w, h = self.window.width, self.window.height
        top = h * 0.68

        self.title = arcade.Text(
            self._title_text, w // 2, top, theme.INK, theme.TITLE,
            font_name=FONT, anchor_x="center")

        self.lines = key_menu(self.window, self._items, top - theme.SPACE_6)

        self.footer = arcade.Text(
            self._footer_text, w // 2, h * 0.14, theme.SUBTLE, theme.SMALL,
            font_name=FONT, anchor_x="center")
        self._built = True

    def on_show_view(self) -> None:
        self.window.background_color = theme.BACKDROP
        if not self._built:
            self.build()

    def on_draw(self) -> None:
        self.clear()
        self.window.default_camera.use()
        if self.title and self.title.text:
            self.title.draw()
        for line in self.lines:
            line.draw()
        if self.footer and self.footer.text:
            self.footer.draw()
