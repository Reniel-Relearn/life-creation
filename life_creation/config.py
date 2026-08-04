"""Every tunable number in Life Creation lives here.

Nothing elsewhere in the codebase should contain a magic number. When the game
feels wrong to play, it should be fixable from this file alone.

This module is pure data. It imports nothing from the game and nothing from a
graphics framework, so both the simulation and the presentation layer may read
it without either one depending on the other.
"""

# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY

DAWN_HOUR = 6
DUSK_HOUR = 18

# The width of the dawn and dusk bands, in hours either side of the boundary.
TWILIGHT_HOURS = 1

# Clock.step is a variable, not a constant (DESIGN.md section 3). The MVP never
# changes it, but the widening time step later depends on it already being one.
DEFAULT_STEP_MINUTES = 10

# ---------------------------------------------------------------------------
# The Rule of Threes (DESIGN.md section 1)
# Minutes for each need to fall from 100 to 0, unopposed.
#
# Air is deliberately absent. DESIGN.md lists it at ~3 minutes, but a breathing
# meter that drains during ordinary play is a chore, not a system. Air is kept
# as future support for exceptional conditions only - drowning, smoke,
# suffocation - and no such condition exists in this slice.
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

# Health only recovers when the body is genuinely provided for.
HEALTH_REGEN_WATER_ABOVE = 25.0
HEALTH_REGEN_FOOD_ABOVE = 25.0
HEALTH_REGEN_WARMTH_ABOVE = 40.0

# ---------------------------------------------------------------------------
# Temperature and warmth
# ---------------------------------------------------------------------------
TEMP_DAY = 19.0            # afternoons let you recover; nights never do
TEMP_NIGHT = 5.0           # temperate, not arctic. Still lethal unsheltered.
TEMP_COMFORT = 18.0        # at or above this, no warmth is lost
TEMP_HARSH = -6.0          # at or below this, warmth drains at the full 3h rate
TEMP_PEAK_HOUR = 15.0      # warmest point of the day
WARMTH_REGAIN_RATE = 100.0 / 120.0  # by a fire: two hours from frozen to warm

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

FIRE_WARMTH_BONUS = 26.0       # degrees added at the fire itself
FIRE_WARMTH_RADIUS = 1         # tiles: how far the heat carries
FIRE_LIGHT_RADIUS = 6          # tiles: how far the light carries

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
FORAGE_YIELD_SPREAD = (0.75, 1.25)
FORAGE_GOOD_ABOVE = 11.0       # message thresholds
FORAGE_FAIR_ABOVE = 6.0

GATHER_MINUTES = 40
GATHER_REST_COST = 5.0
GATHER_WOOD_BASE = 2           # at skill 0.0
GATHER_WOOD_SKILL = 2          # additional at skill 1.0

REST_MINUTES = 60
REST_GAIN = 14.0

SLEEP_MAX_HOURS = 9
SLEEP_DAYTIME_HOURS = 6
SLEEP_GAIN_PER_MINUTE = 100.0 / (8 * MINUTES_PER_HOUR)

STILL_MINUTES = 30
STILL_SPIRIT_GAIN = 0.9

EXHAUSTED_BELOW = 5.0          # below this rest, work is refused

# ---------------------------------------------------------------------------
# Skills - growth by doing
# ---------------------------------------------------------------------------
SKILL_GAIN = 0.012
SKILL_MAX = 1.0
SKILL_MIN_HEADROOM = 0.15      # growth never stops entirely

SKILL_MASTERFUL_ABOVE = 0.85
SKILL_PRACTISED_ABOVE = 0.60
SKILL_CAPABLE_ABOVE = 0.35
SKILL_CLUMSY_ABOVE = 0.12

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

# Spirit widens perception. At full spirit you see one tile further than you
# otherwise would. The player is never told this is happening.
SPIRIT_SIGHT_BONUS = 1
SPIRIT_SIGHT_FULL_AT = 100.0

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

START_AGE_DAYS = 0             # aging is a later phase; the field exists now

# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
MAP_WIDTH = 64
MAP_HEIGHT = 40

RIVER_WIDTH_CHOICES = (1, 1, 2)
RIVER_DRIFT_CHOICES = (-1, 0, 0, 0, 1)
FOREST_CLUMPS, FOREST_SIZE = 9, 42
HILLS_CLUMPS, HILLS_SIZE = 5, 26
BARE_CLUMPS, BARE_SIZE = 4, 14
SCATTER_SPREAD_CHANCE = 0.62
MARSH_CHANCE_BESIDE_WATER = 0.18

GRASS_FORAGE_RANGE = (0, 3)
FOREST_FORAGE_RANGE = (1, 4)
FOREST_WOOD_RANGE = (2, 6)
HILLS_STONE_RANGE = (1, 4)
HILLS_FLINT_CHANCE = 0.30
HILLS_FLINT_RANGE = (1, 2)
MARSH_FORAGE_RANGE = (0, 2)
MARSH_REED_RANGE = (1, 3)

# Spawn. You wake somewhere survivable, not somewhere safe.
SPAWN_WATER_WITHIN = 6
SPAWN_WOOD_WITHIN = 5
SPAWN_FALLBACK_WATER_WITHIN = 8
SPAWN_SEARCH_LIMIT = 12

# A world that fails validation is structurally broken, not merely hard.
# Broken worlds are regenerated from a derived seed; hard ones are kept.
WORLD_MAX_GENERATION_ATTEMPTS = 8
WORLD_MIN_TERRAIN_TYPES = 3
WORLD_MIN_WATER_TILES = 20
WORLD_MIN_FOREST_TILES = 40
WORLD_VALIDATE_WATER_WITHIN = 10
WORLD_VALIDATE_WOOD_WITHIN = 10

# How far you can see. Night is the point at which the world closes in.
SIGHT_DAY = 11
SIGHT_NIGHT = 3
SIGHT_DUSK = 6
SIGHT_FIRE_BONUS = 3

# Crossing running water. Wet and cold, but the river is not a wall.
WADE_MINUTES = 20
WADE_REST_COST = 4.0
WADE_WARMTH_COST = 22.0

# Simulation granularity. Needs are ticked in chunks no larger than this so a
# long sleep cannot skip over the moment of death.
TICK_CHUNK_MINUTES = 15

LOG_LINES = 5
MAX_LOG_ENTRIES = 400          # the log is bounded; nothing grows forever
MAX_CHRONICLE_ENTRIES = 2000

# ---------------------------------------------------------------------------
# Terminal front end (optional debugging interface)
# ---------------------------------------------------------------------------
VIEW_WIDTH = 51
VIEW_HEIGHT = 15

# ---------------------------------------------------------------------------
# Presentation
#
# Read by the graphical layer only. Kept here so the graphical layer has no
# magic numbers of its own, and so config.py stays free of framework imports.
# ---------------------------------------------------------------------------
TILE_SIZE = 40
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 760
WINDOW_TITLE = "Life Creation"

# Turn presentation. The simulation has already resolved by the time any of
# these play; they present a finished turn and never decide one.
MOVE_ANIM_SECONDS = 0.16
WADE_ANIM_SECONDS = 0.34
ACTION_ANIM_SECONDS = 0.30
SLEEP_ANIM_SECONDS = 0.9
DEATH_PAUSE_SECONDS = 2.2

CAMERA_FOLLOW_SPEED = 8.0      # higher is snappier
LIGHT_TRANSITION_SPEED = 1.6   # how fast the ambient tint chases the clock

WATER_ANIM_FRAMES = 4
WATER_ANIM_SECONDS = 0.32
FIRE_ANIM_FRAMES = 4
FIRE_ANIM_SECONDS = 0.12

MAX_PARTICLES = 240
EMBER_LIFETIME = 1.4
EMBERS_PER_FIRE = 3

# Fog of war, as the presentation renders it.
FOG_VISIBLE = 1.0
FOG_REMEMBERED = 0.34
FOG_UNSEEN = 0.0

# Ambient tint per phase, as (r, g, b, a) over the world. Not a black rectangle:
# the per-tile fog shading and the fire light both sit outside this layer.
AMBIENT_TINT = {
    "dawn": (70, 60, 96, 70),
    "day": (255, 250, 230, 0),
    "dusk": (96, 58, 62, 92),
    "night": (14, 20, 54, 170),
}

TEXT_FONT = ("Consolas", "Courier New", "calibri")

# ---------------------------------------------------------------------------
# Automated agents (tools/simulate.py)
#
# Not game balance - these are the thresholds the rule-based test agents play
# by. They live here so no numbers hide in the harness either.
# ---------------------------------------------------------------------------
AGENT_FIRE_TOP_UP_BELOW = 240.0     # minutes of fuel left before feeding
AGENT_SLEEP_REST_BELOW = 70.0
AGENT_COLD_BELOW = 40.0
AGENT_THIRSTY_BELOW = 45.0
AGENT_HUNGRY_BELOW = 45.0
AGENT_TIRED_BELOW = 35.0
AGENT_WOOD_TARGET = 8
AGENT_DUSK_LEAD_HOURS = 2           # start preparing this long before dusk
AGENT_MAX_TURNS = 600               # a life that never ends is a bug
AGENT_STUCK_AFTER = 25              # consecutive refused actions = a live-lock

