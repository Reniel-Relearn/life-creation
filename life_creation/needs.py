"""Body, Soul and Spirit.

Three needs on three timescales (DESIGN.md section 1):

    Body   - kills you.     Shown as numbers.
    Soul   - narrows you.   Described in prose, never numbered.
    Spirit - does nothing when neglected. Never displayed at all.
"""

from dataclasses import dataclass

from . import config


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass
class Needs:
    # Body - the player sees these
    water: float = config.START_WATER
    food: float = config.START_FOOD
    warmth: float = config.START_WARMTH
    rest: float = config.START_REST
    health: float = config.START_HEALTH

    # Soul - the player is told about this in words
    soul: float = config.START_SOUL

    # Spirit - the player is never shown this
    spirit: float = config.START_SPIRIT

    death_cause: str | None = None

    # -- derived ------------------------------------------------------------

    @property
    def alive(self) -> bool:
        return self.health > 0.0

    @property
    def vigour(self) -> float:
        """How much work the body still has in it.

        Hunger does not kill quickly; it weakens quickly. Everything you do
        costs more when you are empty.
        """
        from_food = 0.45 + 0.55 * (self.food / 100.0)
        from_health = 0.50 + 0.50 * (self.health / 100.0)
        return max(0.25, from_food * from_health)

    @property
    def exhausted(self) -> bool:
        return self.rest < config.EXHAUSTED_BELOW

    # -- the tick -----------------------------------------------------------

    def tick(self, minutes: float, effective_temp: float,
             monotony_penalty: float = 0.0, resting: bool = False) -> None:
        """Advance all six needs by `minutes` of game time."""
        if minutes <= 0:
            return

        self.water -= config.WATER_RATE * minutes
        self.food -= config.FOOD_RATE * minutes
        if not resting:
            self.rest -= config.REST_RATE * minutes

        self._tick_warmth(minutes, effective_temp)
        self._tick_soul(minutes, monotony_penalty)
        self.spirit -= config.SPIRIT_RATE * minutes

        self._tick_health(minutes)
        self.clamp()

    def _tick_warmth(self, minutes: float, effective_temp: float) -> None:
        if effective_temp >= config.TEMP_COMFORT:
            self.warmth += config.WARMTH_REGAIN_RATE * minutes
            return
        span = config.TEMP_COMFORT - config.TEMP_HARSH
        exposure = (config.TEMP_COMFORT - effective_temp) / span
        exposure = max(0.0, min(1.0, exposure))
        self.warmth -= config.WARMTH_RATE * exposure * minutes

    def _tick_soul(self, minutes: float, monotony_penalty: float) -> None:
        decay = config.SOUL_RATE * minutes
        # Spirit sustains soul under hardship.
        shelter = (self.spirit / 100.0) * config.SPIRIT_SOUL_SHELTER
        decay *= (1.0 - shelter)
        self.soul -= decay + monotony_penalty

    def _tick_health(self, minutes: float) -> None:
        damage = 0.0
        cause = None
        if self.warmth <= 0.0:
            damage += config.HEALTH_LOSS_FREEZING * minutes
            cause = "cold"
        if self.water <= 0.0:
            damage += config.HEALTH_LOSS_DEHYDRATED * minutes
            cause = cause or "thirst"
        if self.food <= 0.0:
            damage += config.HEALTH_LOSS_STARVING * minutes
            cause = cause or "hunger"

        if damage > 0.0:
            self.health -= damage
            if self.health <= 0.0 and self.death_cause is None:
                self.death_cause = cause
        elif (self.water > config.HEALTH_REGEN_WATER_ABOVE
                and self.food > config.HEALTH_REGEN_FOOD_ABOVE
                and self.warmth > config.HEALTH_REGEN_WARMTH_ABOVE):
            self.health += config.HEALTH_REGEN * minutes

    def clamp(self) -> None:
        """Hold every need inside 0..100.

        Actions and discovery add to needs directly, outside the tick, so this
        has to be callable from outside too.
        """
        self.water = _clamp(self.water)
        self.food = _clamp(self.food)
        self.warmth = _clamp(self.warmth)
        self.rest = _clamp(self.rest)
        self.health = _clamp(self.health)
        self.soul = _clamp(self.soul)
        self.spirit = _clamp(self.spirit)

    # -- the body's own warnings -------------------------------------------

    def urgent_warning(self) -> str | None:
        """The loudest thing the body is currently saying."""
        if self.warmth <= 0:
            return "You are freezing."
        if self.water <= 0:
            return "You are dying of thirst."
        if self.food <= 0:
            return "You are starving."
        if self.warmth < 20:
            return "You are dangerously cold."
        if self.water < 20:
            return "Your throat is raw with thirst."
        if self.rest < 15:
            return "You can barely stand."
        if self.food < 20:
            return "Hunger is hollowing you out."
        return None

    # -- soul, in words -----------------------------------------------------

    def describe_soul(self) -> str:
        s = self.soul
        if s >= 85:
            return "There is more of this place to see."
        if s >= 70:
            return ""
        if s >= 55:
            return "You have been here a long time."
        if s >= 40:
            return "You are tired of this valley."
        if s >= 25:
            return "The days have begun to blur together."
        if s >= 10:
            return "You do not think much anymore."
        return "You go on because going on is what you do."
