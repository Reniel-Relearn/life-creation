"""Sound.

Entirely optional. The project ships no audio files - there is no copyrighted
music or sound in it - so in practice this is a working architecture playing
nothing. Drop a `.wav` into `assets/audio/` and it starts being used.

Every call is safe when the sound is missing.
"""

from __future__ import annotations

import logging

from ..outcomes import EventKind, Outcome
from .assets import Assets

log = logging.getLogger(__name__)

# Which event asks for which sound. Names that are not present stay silent.
_EVENT_SOUNDS = {
    EventKind.MOVED: "footstep",
    EventKind.WADED: "river",
    EventKind.DRANK: "river",
    EventKind.FIRE_LIT: "fire",
    EventKind.FIRE_FED: "fire",
}


class Audio:
    def __init__(self, assets: Assets, enabled: bool = True):
        self.assets = assets
        self.enabled = enabled
        self._ambience = None

    def play(self, name: str, volume: float = 0.6) -> None:
        if not self.enabled:
            return
        sound = self.assets.sounds.get(name)
        if sound is None:
            return
        try:
            sound.play(volume=volume)
        except Exception as exc:      # a dead audio device must not end the run
            log.warning("could not play %s (%s); muting audio", name, exc)
            self.enabled = False

    def for_outcome(self, outcome: Outcome) -> None:
        for event in outcome.events:
            name = _EVENT_SOUNDS.get(event.kind)
            if name:
                self.play(name)
                return

    def transition(self) -> None:
        self.play("transition", volume=0.4)
