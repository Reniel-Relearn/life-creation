"""The interface, kept quiet.

Body is bars, because Body is loud and kills you. Soul is one line of prose
that is easy to miss. Spirit is not here, and there is a test that proves the
data this module receives does not contain it.
"""

from __future__ import annotations

import arcade

from .. import config
from ..viewmodel import PlayView
from .input import DISPLAY_KEY

FONT = config.TEXT_FONT

INK = (214, 214, 222)
DIM = (128, 128, 142)
FAINT = (86, 86, 98)
WARN = (206, 104, 92)
SOUL = (134, 132, 168)
PANEL = (10, 12, 18, 165)

BAR_WIDTH = 128
BAR_HEIGHT = 9
BAR_GAP = 22
MARGIN = 22

LOG_TOP = 86            # below the clock, the place line and the warning
LOG_LINE_HEIGHT = 16
LOG_PANEL_WIDTH = 460
# The panel is sized from what goes in it, so the log can never spill onto the
# map the way it did when this was a fixed height.
TOP_PANEL_HEIGHT = MARGIN + LOG_TOP + config.LOG_LINES * LOG_LINE_HEIGHT
BOTTOM_PANEL_HEIGHT = MARGIN + 108


def _bar_colour(value: float) -> tuple[int, int, int]:
    if value >= 60:
        return (108, 156, 118)
    if value >= 30:
        return (198, 162, 62)
    return (188, 92, 82)


class Hud:
    """Text objects are built once and mutated. Nothing is allocated per frame."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.when = arcade.Text("", MARGIN, height - MARGIN - 14, INK, 15,
                                font_name=FONT, bold=True)
        self.place = arcade.Text("", MARGIN, height - MARGIN - 36, DIM, 11,
                                 font_name=FONT)
        self.warning = arcade.Text("", MARGIN, height - MARGIN - 56, WARN, 12,
                                   font_name=FONT, bold=True)

        self.soul = arcade.Text("", width // 2, MARGIN + 128, SOUL, 12,
                                font_name=FONT, anchor_x="center", italic=True)

        self.flash = arcade.Text("", width // 2, height // 2 - 120, INK, 14,
                                 font_name=FONT, anchor_x="center")

        self.inventory = arcade.Text("", width - MARGIN, MARGIN + 10, DIM, 12,
                                     font_name=FONT, anchor_x="right")

        self._bar_labels = [
            arcade.Text("", MARGIN, 0, DIM, 10, font_name=FONT)
            for _ in range(5)
        ]
        self._bar_values = [
            arcade.Text("", 0, 0, DIM, 10, font_name=FONT)
            for _ in range(5)
        ]
        # Left-aligned in a block that is itself centred, so the keys line up
        # in a column instead of ragging around the middle of the screen.
        self._prompts = [
            arcade.Text("", width // 2 - 130, 0, INK, 12, font_name=FONT)
            for _ in range(6)
        ]
        self._log = [
            arcade.Text("", MARGIN, 0, FAINT, 11, font_name=FONT)
            for _ in range(config.LOG_LINES)
        ]

        self._body: tuple = ()
        self._prompt_count = 0
        self._flash_left = 0.0

    # -- state --------------------------------------------------------------

    def update(self, view: PlayView) -> None:
        self.when.text = f"Day {view.day}    {view.time_text}    {view.phase.value}"

        place = f"You are standing in {view.standing_in}."
        if view.at_a_fire:
            place += "   A fire is burning here."
        self.place.text = place
        self.warning.text = view.warning
        self.soul.text = view.soul_line
        self._body = view.body

        for i, reading in enumerate(view.body):
            y = MARGIN + 88 - i * BAR_GAP
            self._bar_labels[i].text = reading.label
            self._bar_labels[i].y = y - 4
            self._bar_values[i].text = str(int(reading.value))
            self._bar_values[i].x = MARGIN + 78 + BAR_WIDTH + 10
            self._bar_values[i].y = y - 4

        self._prompt_count = min(len(view.prompts), len(self._prompts))
        for i in range(self._prompt_count):
            prompt = view.prompts[i]
            text = self._prompts[i]
            shown = DISPLAY_KEY.get(prompt.key, prompt.key.upper())
            text.text = f"{shown}  {prompt.text}"
            text.y = MARGIN + 86 - i * 18

        for i, line in enumerate(reversed(view.log)):
            if i >= len(self._log):
                break
            self._log[i].text = line
            self._log[i].y = self.height - MARGIN - LOG_TOP - i * LOG_LINE_HEIGHT
            self._log[i].color = (*FAINT, max(60, 200 - i * 34))

        if view.inventory:
            self.inventory.text = "   ".join(
                f"{name} {count}" for name, count in view.inventory)
        else:
            self.inventory.text = "you carry nothing"

    def say(self, message: str, seconds: float = 2.4) -> None:
        self.flash.text = message
        self._flash_left = seconds

    def update_animation(self, delta_time: float) -> None:
        if self._flash_left > 0:
            self._flash_left = max(0.0, self._flash_left - delta_time)

    # -- drawing ------------------------------------------------------------

    def draw(self) -> None:
        self._panel(0, 0, self.width, BOTTOM_PANEL_HEIGHT)
        self._panel(0, self.height - TOP_PANEL_HEIGHT,
                    LOG_PANEL_WIDTH, TOP_PANEL_HEIGHT)

        self.when.draw()
        self.place.draw()
        if self.warning.text:
            self.warning.draw()
        for text in self._log:
            if text.text:
                text.draw()

        for i, reading in enumerate(self._body):
            y = MARGIN + 88 - i * BAR_GAP
            x = MARGIN + 74
            arcade.draw_lbwh_rectangle_filled(
                x, y - BAR_HEIGHT / 2, BAR_WIDTH, BAR_HEIGHT, (30, 32, 40))
            filled = BAR_WIDTH * max(0.0, min(100.0, reading.value)) / 100.0
            if filled > 0:
                arcade.draw_lbwh_rectangle_filled(
                    x, y - BAR_HEIGHT / 2, filled, BAR_HEIGHT,
                    _bar_colour(reading.value))
            self._bar_labels[i].draw()
            self._bar_values[i].draw()

        for i in range(self._prompt_count):
            self._prompts[i].draw()

        if self.soul.text:
            self.soul.draw()
        self.inventory.draw()

        if self._flash_left > 0 and self.flash.text:
            self.flash.color = (*INK, int(255 * min(1.0, self._flash_left / 0.6)))
            self.flash.draw()

    @staticmethod
    def _panel(x: float, y: float, w: float, h: float) -> None:
        arcade.draw_lbwh_rectangle_filled(x, y, w, h, PANEL)
