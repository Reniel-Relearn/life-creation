"""The interface, kept quiet.

Body is bars, because Body is loud and kills you. Soul is one line of prose
that is easy to miss. Spirit is not here, and there is a test that proves the
data this module receives does not contain it.

Everything is laid out on the 8pt grid in `theme.py` and drawn on gradient
scrims rather than panels, so the interface sits on darkness that fades into
the world instead of cutting a hard seam across it.
"""

from __future__ import annotations

import arcade

from .. import config
from ..viewmodel import PlayView
from . import theme
from .input import DISPLAY_KEY

FONT = config.TEXT_FONT
MARGIN = theme.MARGIN

BAR_WIDTH = 132
BAR_HEIGHT = 6
BAR_ROW = 20
BAR_LABEL_W = 62

LOG_LINE = theme.line_step(theme.SMALL)
LOG_WIDTH = 760

TOP_SCRIM = 210
BOTTOM_SCRIM = 168


def _bar_colour(value: float) -> tuple[int, int, int]:
    if value >= 60:
        return theme.BAR_GOOD
    if value >= 30:
        return theme.BAR_WARN
    return theme.BAR_BAD


class Hud:
    """Text objects are built once and mutated. Nothing is allocated per frame."""

    def __init__(self, width: int, height: int,
                 scrim: arcade.Texture | None = None,
                 scrim_top: arcade.Texture | None = None,
                 scrim_corner: arcade.Texture | None = None):
        self.width = width
        self.height = height
        self.scrim = scrim
        self.scrim_top = scrim_top
        self.scrim_corner = scrim_corner

        top = height - MARGIN - theme.HEADING
        self.when = arcade.Text("", MARGIN, top, theme.INK, theme.HEADING,
                                font_name=FONT)
        self.place = arcade.Text("", MARGIN, top - theme.SPACE_3, theme.MUTED,
                                 theme.SMALL, font_name=FONT)
        self.warning = arcade.Text("", MARGIN, top - theme.SPACE_3 - theme.SPACE_2,
                                   theme.ALARM, theme.SMALL, font_name=FONT)

        self._log_top = top - theme.SPACE_6 - theme.SPACE_1
        self._log = [
            arcade.Text("", MARGIN, self._log_top - i * LOG_LINE,
                        theme.SUBTLE, theme.SMALL, font_name=FONT)
            for i in range(config.LOG_LINES)
        ]

        # Body, bottom left.
        self._bar_labels = [
            arcade.Text("", MARGIN, 0, theme.MUTED, theme.MICRO, font_name=FONT)
            for _ in range(5)
        ]
        self._bar_values = [
            arcade.Text("", MARGIN + BAR_LABEL_W + BAR_WIDTH + theme.SPACE_1, 0,
                        theme.SUBTLE, theme.MICRO, font_name=FONT)
            for _ in range(5)
        ]

        # Prompts, bottom centre, left-aligned on one axis so the keys line up.
        prompt_x = width // 2 - 140
        self._prompts = [
            arcade.Text("", prompt_x + 34, 0, theme.INK, theme.BODY,
                        font_name=FONT)
            for _ in range(6)
        ]
        self._prompt_keys = [
            arcade.Text("", prompt_x, 0, theme.EMBER, theme.BODY, font_name=FONT)
            for _ in range(6)
        ]

        self.soul = arcade.Text("", width // 2, 0, theme.SOUL, theme.SMALL,
                                font_name=FONT, anchor_x="center", italic=True)
        self.inventory = arcade.Text("", width - MARGIN, MARGIN, theme.MUTED,
                                     theme.SMALL, font_name=FONT,
                                     anchor_x="right")
        self.flash = arcade.Text("", width // 2, height // 2 - 132, theme.INK,
                                 theme.BODY, font_name=FONT, anchor_x="center")

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
        self._body = view.body

        bar_top = MARGIN + theme.SPACE_2 + BAR_ROW * 4
        for i, reading in enumerate(view.body):
            y = bar_top - i * BAR_ROW
            self._bar_labels[i].text = reading.label
            self._bar_labels[i].y = y - 4
            self._bar_values[i].text = str(int(reading.value))
            self._bar_values[i].y = y - 4

        self._prompt_count = min(len(view.prompts), len(self._prompts))
        prompt_top = MARGIN + theme.SPACE_1 + (self._prompt_count - 1) * BAR_ROW
        for i in range(self._prompt_count):
            prompt = view.prompts[i]
            y = prompt_top - i * BAR_ROW
            self._prompt_keys[i].text = DISPLAY_KEY.get(prompt.key,
                                                        prompt.key.upper())
            self._prompt_keys[i].y = y
            self._prompts[i].text = prompt.text
            self._prompts[i].y = y

        self.soul.text = view.soul_line
        self.soul.y = MARGIN + BOTTOM_SCRIM - theme.SPACE_3

        for i, line in enumerate(reversed(view.log)):
            if i >= len(self._log):
                break
            self._log[i].text = line
            # The most recent line is the brightest; older ones recede.
            self._log[i].color = theme.with_alpha(theme.SUBTLE,
                                                  max(0.34, 1.0 - i * 0.18))

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
        self._scrims()

        self.when.draw()
        self.place.draw()
        if self.warning.text:
            self.warning.draw()
        for text in self._log:
            if text.text:
                text.draw()

        bar_top = MARGIN + theme.SPACE_2 + BAR_ROW * 4
        for i, reading in enumerate(self._body):
            y = bar_top - i * BAR_ROW
            x = MARGIN + BAR_LABEL_W
            arcade.draw_lbwh_rectangle_filled(
                x, y - BAR_HEIGHT / 2, BAR_WIDTH, BAR_HEIGHT, theme.BAR_TRACK)
            filled = BAR_WIDTH * max(0.0, min(100.0, reading.value)) / 100.0
            if filled > 0:
                arcade.draw_lbwh_rectangle_filled(
                    x, y - BAR_HEIGHT / 2, filled, BAR_HEIGHT,
                    _bar_colour(reading.value))
            self._bar_labels[i].draw()
            self._bar_values[i].draw()

        for i in range(self._prompt_count):
            self._prompt_keys[i].draw()
            self._prompts[i].draw()

        if self.soul.text:
            self.soul.draw()
        self.inventory.draw()

        if self._flash_left > 0 and self.flash.text:
            self.flash.color = theme.with_alpha(
                theme.INK, min(1.0, self._flash_left / 0.6))
            self.flash.draw()

    def _scrims(self) -> None:
        """Gradient washes, not panels. No hard edge anywhere on the screen."""
        if self.scrim is not None:
            arcade.draw_texture_rect(
                self.scrim, arcade.LBWH(0, 0, self.width, BOTTOM_SCRIM))
        corner = self.scrim_corner or self.scrim_top
        if corner is not None:
            arcade.draw_texture_rect(
                corner,
                arcade.LBWH(0, self.height - TOP_SCRIM, LOG_WIDTH, TOP_SCRIM))
