"""Every tunable number in Life Creation lives here.

Nothing elsewhere in the codebase should contain a magic number. When the game
feels wrong to play, it should be fixable from this file alone.
"""

# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY

DAWN_HOUR = 6
DUSK_HOUR = 18

# Clock.step is a variable, not a constant (DESIGN.md section 3). The MVP never
# changes it, but the widening time step later depends on it already being one.
DEFAULT_STEP_MINUTES = 10

# ---------------------------------------------------------------------------
# The Rule of Threes (DESIGN.md section 1)
# Minutes for each need to fall from 100 to 0, unopposed.
# ---------------------------------------------------------------------------
WATER_EMPTY_MINUTES = 3 * MINUTES_PER_DAY          # 3 days
FOOD_EMPTY_MINUTES = 21 * MINUTES_PER_DAY          # 3 weeks
WARMTH_EMPTY_MINUTES = 3 * MINUTES_PER_HOUR        # 3 hours, fully exposed
REST_EMPTY_MINUTES = 36 * MINUTES_PER_HOUR         # a body can be pushed
SOUL_EMPTY_MINUTES = 90 * MINUTES_PER_DAY          # 3 months
SPIRIT_EMPTY_MINUTES = 3 * 365 * MINUTES_PER_DAY   # 3 years

WATER_RATE = 100.0 / WATER_EMPTY_MINUTES
FOOD_RATE = 100.0 / FOOD_EMPTY_MINUTES
WARMTH_RATE = 100.0 / WARMTH_EMPTY_MINUTES
REST_RATE = 100.0 / REST_EMPTY_MINUTES
SOUL_RATE = 100.0 / SOUL_EMPTY_MINUTES
SPIRIT_RATE = 100.0 / SPIRIT_EMPTY_MINUTES

# ---------------------------------------------------------------------------
# Health - what actually kills you.
# Cold is the ambush, water is the emergency, food is the strategy.
# ---------------------------------------------------------------------------
HEALTH_LOSS_FREEZING = 100.0 / (2 * MINUTES_PER_HOUR)    # 2h at zero warmth
HEALTH_LOSS_DEHYDRATED = 100.0 / (1 * MINUTES_PER_DAY)   # 1 day at zero water
HEALTH_LOSS_STARVING = 100.0 / (3 * MINUTES_PER_DAY)     # 3 days at zero food
HEALTH_REGEN = 100.0 / (7 * MINUTES_PER_DAY)             # when all needs are met

# ---------------------------------------------------------------------------
# Temperature and warmth
# ---------------------------------------------------------------------------
TEMP_DAY = 19.0            # afternoons let you recover; nights never do
TEMP_NIGHT = 5.0           # temperate, not arctic. Still lethal unsheltered.
TEMP_COMFORT = 18.0        # at or above this, no warmth is lost
TEMP_HARSH = -6.0          # at or below this, warmth drains at the full 3h rate
WARMTH_REGAIN_RATE = 100.0 / 120.0  # by a fire: two hours from frozen to warm

FIRE_WARMTH_BONUS = 26.0   # degrees added while standing at a lit fire

# ---------------------------------------------------------------------------
# Fire - the first real gate
# ---------------------------------------------------------------------------
FIRE_FUEL_PER_WOOD = 120       # minutes of burn bought by one unit of wood
FIRE_MAX_FUEL = 720
FIREMAKING_BASE_CHANCE = 0.25  # at skill 0.0
FIREMAKING_SKILL_BONUS = 0.60  # at skill 1.0 the chance is 0.85
FIREMAKING_MINUTES = 25
FIREMAKING_REST_COST = 5.0
FEED_FIRE_MINUTES = 5

# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
MOVE_MINUTES = 12
MOVE_REST_COST = 1.2

DRINK_MINUTES = 5
DRINK_WATER_GAIN = 55.0
MARSH_WATER_FACTOR = 0.5       # still water slakes less and (later) sickens

FORAGE_MINUTES = 45
FORAGE_REST_COST = 4.0
FORAGE_FOOD_BASE = 5.0         # at skill 0.0
FORAGE_FOOD_SKILL = 9.0        # additional at skill 1.0

GATHER_MINUTES = 40
GATHER_REST_COST = 5.0
GATHER_WOOD_BASE = 2           # at skill 0.0
GATHER_WOOD_SKILL = 2          # additional at skill 1.0

REST_MINUTES = 60
REST_GAIN = 14.0

SLEEP_MAX_HOURS = 9
SLEEP_GAIN_PER_MINUTE = 100.0 / (8 * MINUTES_PER_HOUR)

STILL_MINUTES = 30
STILL_SPIRIT_GAIN = 0.9

EXHAUSTED_BELOW = 5.0          # below this rest, work is refused

# ---------------------------------------------------------------------------
# Skills - growth by doing
# ---------------------------------------------------------------------------
SKILL_GAIN = 0.012
SKILL_MAX = 1.0

# ---------------------------------------------------------------------------
# Soul and Spirit
# ---------------------------------------------------------------------------
SOUL_PER_NEW_TILE = 0.02       # curiosity feeds the soul
SOUL_PER_NIGHT_SURVIVED = 1.5
SOUL_PER_FIRST_FIRE = 6.0
MONOTONY_THRESHOLD = 5         # same action this many times in a row
MONOTONY_SOUL_PENALTY = 0.35   # per repeat beyond the threshold

# Spirit sustains soul: at full spirit, soul decays at half speed.
SPIRIT_SOUL_SHELTER = 0.5

# Below this, stillness stops occurring to you. Nothing is announced.
SOUL_STILLNESS_LOST_BELOW = 30.0

# ---------------------------------------------------------------------------
# Starting condition - you wake with nothing
# ---------------------------------------------------------------------------
START_WATER = 80.0
START_FOOD = 70.0
START_WARMTH = 75.0
START_REST = 90.0
START_HEALTH = 100.0
START_SOUL = 70.0
START_SPIRIT = 50.0

# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
MAP_WIDTH = 64
MAP_HEIGHT = 40
VIEW_WIDTH = 51
VIEW_HEIGHT = 15

# How far you can see. Night is the point at which the world closes in.
SIGHT_DAY = 11
SIGHT_NIGHT = 3
SIGHT_FIRE_BONUS = 3

# Crossing running water. Wet and cold, but the river is not a wall.
WADE_MINUTES = 20
WADE_REST_COST = 4.0
WADE_WARMTH_COST = 22.0

# Simulation granularity. Needs are ticked in chunks no larger than this so a
# long sleep cannot skip over the moment of death.
TICK_CHUNK_MINUTES = 15

LOG_LINES = 5

# The windowed front end has room for more map than a terminal does.
WINDOW_VIEW_WIDTH = 63
WINDOW_VIEW_HEIGHT = 27
WINDOW_LOG_LINES = 6
WINDOW_FONT = ("Consolas", 14)
WINDOW_FONT_SMALL = ("Consolas", 11)
