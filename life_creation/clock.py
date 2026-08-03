"""Game time.

One authoritative clock, measured in minutes since the character woke. `step`
is a variable, not a constant - the MVP never changes it, but the widening time
step later (hours to days to seasons) depends on it already being one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from . import config


class Phase(str, Enum):
    DAWN = "dawn"
    DAY = "day"
    DUSK = "dusk"
    NIGHT = "night"


@dataclass
class Clock:
    # You wake at dawn with a full day in front of you. The first night is the
    # game's first real gate, and it has to be reachable.
    minutes: int = config.DAWN_HOUR * config.MINUTES_PER_HOUR
    step: int = config.DEFAULT_STEP_MINUTES

    # Debug time acceleration. 1.0 in ordinary play; only the developer flags
    # in main.py ever set it to anything else.
    scale: float = 1.0

    def advance(self, minutes: float) -> None:
        self.minutes += int(minutes)

    def scaled(self, minutes: float) -> float:
        """Apply debug acceleration to a cost in minutes."""
        return minutes * self.scale

    # -- readings -----------------------------------------------------------

    @property
    def day(self) -> int:
        """Days lived, 1-indexed. You wake on day 1."""
        return self.minutes // config.MINUTES_PER_DAY + 1

    @property
    def minute_of_day(self) -> int:
        return self.minutes % config.MINUTES_PER_DAY

    @property
    def hour(self) -> int:
        return self.minute_of_day // config.MINUTES_PER_HOUR

    @property
    def minute(self) -> int:
        return self.minute_of_day % config.MINUTES_PER_HOUR

    @property
    def is_night(self) -> bool:
        return not (config.DAWN_HOUR <= self.hour < config.DUSK_HOUR)

    @property
    def phase(self) -> Phase:
        h = self.hour
        if h < config.DAWN_HOUR - config.TWILIGHT_HOURS:
            return Phase.NIGHT
        if h < config.DAWN_HOUR + config.TWILIGHT_HOURS:
            return Phase.DAWN
        if h < config.DUSK_HOUR - config.TWILIGHT_HOURS:
            return Phase.DAY
        if h < config.DUSK_HOUR + config.TWILIGHT_HOURS:
            return Phase.DUSK
        return Phase.NIGHT

    def clock_text(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def minutes_until_hour(self, target_hour: int) -> int:
        """Minutes from now until the next occurrence of `target_hour`."""
        target = target_hour * config.MINUTES_PER_HOUR
        now = self.minute_of_day
        delta = target - now
        if delta <= 0:
            delta += config.MINUTES_PER_DAY
        return delta

    def minutes_until_dawn(self) -> int:
        return self.minutes_until_hour(config.DAWN_HOUR)

    def ambient_temperature(self) -> float:
        """A smooth day/night temperature curve.

        Coldest just before dawn, warmest mid-afternoon. Cold is the fastest
        killer in the game, so this curve matters more than it looks.
        """
        fraction = self.minute_of_day / config.MINUTES_PER_DAY
        angle = 2 * math.pi * (fraction - (config.TEMP_PEAK_HOUR / config.HOURS_PER_DAY))
        swing = (config.TEMP_DAY - config.TEMP_NIGHT) / 2.0
        midpoint = (config.TEMP_DAY + config.TEMP_NIGHT) / 2.0
        return midpoint + swing * math.cos(angle)
