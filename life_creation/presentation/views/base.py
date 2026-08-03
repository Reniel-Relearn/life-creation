"""Shared furniture for the quiet screens.

The opening, the pause, the help and the chronicle are all the same shape: a
dark field, a little text, and nothing hurrying the player along.
"""

from __future__ import annotations

import arcade

from ... import config

BACKDROP = (12, 13, 18)
INK = (222, 222, 230)
DIM = (140, 140, 154)
FAINT = (84, 84, 96)
FONT = config.TEXT_FONT


class Quiet(arcade.View):
    """A centred column of text on a dark field."""

    def __init__(self, title: str = "", lines: tuple[str, ...] = (),
                 footer: str = ""):
        super().__init__()
        self._title_text = title
        self._lines_text = lines
        self._footer_text = footer
        self._built = False
        self.title: arcade.Text | None = None
        self.lines: list[arcade.Text] = []
        self.footer: arcade.Text | None = None

    def build(self) -> None:
        w, h = self.window.width, self.window.height
        top = h * 0.72

        self.title = arcade.Text(
            self._title_text, w // 2, top, INK, 26, font_name=FONT,
            anchor_x="center", bold=True)

        self.lines = []
        for i, line in enumerate(self._lines_text):
            self.lines.append(arcade.Text(
                line, w // 2, top - 70 - i * 28, DIM, 14, font_name=FONT,
                anchor_x="center"))

        self.footer = arcade.Text(
            self._footer_text, w // 2, h * 0.12, FAINT, 12, font_name=FONT,
            anchor_x="center")
        self._built = True

    def on_show_view(self) -> None:
        self.window.background_color = BACKDROP
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
