"""Pause.

Opening this does not advance the clock. Nothing in the world moves while it
is up, because nothing in the world moves except when a turn resolves.
"""

from __future__ import annotations

import arcade

from .base import Quiet


class PauseView(Quiet):
    def __init__(self, app, play_view):
        super().__init__(
            title="Paused",
            lines=(
                "Esc      back to the world",
                "H        controls",
                "N        begin another life",
                "Ctrl+Q   quit",
            ),
            footer="Nothing moves while this is open.",
        )
        self.app = app
        self.play_view = play_view

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(self.play_view)
        elif symbol == arcade.key.H:
            self.app.show_help(back_to=self)
        elif symbol == arcade.key.N:
            self.app.show_naming()
        elif symbol == arcade.key.Q and (modifiers & arcade.key.MOD_CTRL):
            self.window.close()
