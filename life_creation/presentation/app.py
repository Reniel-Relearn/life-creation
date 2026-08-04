"""The window, and the screens it shows.

This is the top of the stack. It owns the framework, the assets and the view
transitions, and it hands every player action down to the controller. It
contains no survival rule of any kind.
"""

from __future__ import annotations

import logging

import arcade

from .. import config
from ..application import Session
from . import assets as assets_mod
from .audio import Audio
from .views import (ChronicleView, GameView, HelpView, NamingView, OpeningView,
                    PauseView)

log = logging.getLogger(__name__)


class LifeCreation(arcade.Window):
    def __init__(self, seed: int | None = None, time_scale: float = 1.0,
                 debug: bool = False, muted: bool = False,
                 visible: bool = True):
        super().__init__(
            config.WINDOW_WIDTH, config.WINDOW_HEIGHT, config.WINDOW_TITLE,
            visible=visible, vsync=True,
        )
        self.seed = seed
        self.time_scale = time_scale
        self.debug = debug

        self.assets = assets_mod.load()
        self.audio = Audio(self.assets, enabled=not muted)
        if self.assets.missing:
            log.info("optional assets not present (this is fine): %s",
                     ", ".join(self.assets.missing))

        self.session: Session | None = None

    # -- screens ------------------------------------------------------------

    def show_opening(self) -> OpeningView:
        view = OpeningView(self)
        self.show_view(view)
        return view

    def show_naming(self) -> NamingView:
        view = NamingView(self, default_seed=self.seed)
        self.show_view(view)
        return view

    def show_help(self, back_to: arcade.View) -> HelpView:
        view = HelpView(self, back_to)
        self.show_view(view)
        return view

    def show_pause(self, play_view: GameView) -> PauseView:
        view = PauseView(self, play_view)
        self.show_view(view)
        return view

    def show_chronicle(self, session: Session) -> ChronicleView:
        view = ChronicleView(self, session)
        self.show_view(view)
        return view

    # -- runs ---------------------------------------------------------------

    def begin_run(self, name: str, seed: int | None = None) -> GameView:
        """Start a life. Called for the first run and for every restart."""
        self.session = Session(name, seed if seed is not None else self.seed,
                               time_scale=self.time_scale)
        self.session.game.say("You wake with nothing.")
        log.info("run: name=%s seed=%s", name, self.session.seed)
        view = GameView(self, self.session)
        self.show_view(view)
        return view


def run(seed: int | None = None, time_scale: float = 1.0,
        debug: bool = False, muted: bool = False) -> int:
    window = LifeCreation(seed=seed, time_scale=time_scale, debug=debug,
                          muted=muted)
    window.show_opening()
    arcade.run()
    return 0
