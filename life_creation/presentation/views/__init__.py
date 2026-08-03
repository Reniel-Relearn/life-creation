"""Screens. One file per screen, and none of them owns a rule."""

from .ending import ChronicleView
from .help import HelpView
from .naming import NamingView
from .opening import OpeningView
from .pause import PauseView
from .play import GameView

__all__ = [
    "ChronicleView", "GameView", "HelpView", "NamingView", "OpeningView",
    "PauseView",
]
