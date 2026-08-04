"""The look of the game, in one place.

Two rules hold this file together.

**Contrast.** Every colour that carries meaning clears WCAG AA (4.5:1) against
the backdrop. The old palette had a `FAINT` grey at 2.68:1 doing real work in
the opening menu and the event log, which is why both looked washed out.
Anything below the line here is decorative and never the only way to read
something.

**A strict type scale.** Six sizes, no in-between, and bold reserved for two
places. A monospace face loses its character when it is bolded and rescaled at
whim, and the old HUD used eleven different sizes.

The palette is a cold world with one warm thing in it. Everything is slate and
ash except fire, which is the only warm colour in the game and the only thing
that keeps you alive.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Surface
# ---------------------------------------------------------------------------
# A tinted slate rather than pure black. Flat black reads as "nothing rendered
# here"; a cool near-black reads as night.
BACKDROP = (14, 17, 26)
UNKNOWN_LAND = (19, 22, 32)      # the world beyond what you have seen
SCRIM = (9, 11, 17)              # gradient wash behind the HUD

# ---------------------------------------------------------------------------
# Ink — all AA or better on BACKDROP
# ---------------------------------------------------------------------------
INK = (228, 230, 237)            # 15.1:1  primary
MUTED = (168, 173, 189)          #  8.4:1  secondary
SUBTLE = (126, 132, 150)         #  5.1:1  tertiary, still readable
DECOR = (62, 68, 82)             # decorative only: rules, empty bar tracks

# ---------------------------------------------------------------------------
# Meaning
# ---------------------------------------------------------------------------
EMBER = (217, 130, 43)           #  6.5:1  fire, warmth, the one warm colour
SOUL = (150, 150, 190)           #  6.7:1  the soul line, never a number
ALARM = (214, 106, 96)           #  6.0:1  the body shouting

BAR_GOOD = (110, 158, 118)
BAR_WARN = (200, 160, 60)
BAR_BAD = (192, 96, 90)
BAR_TRACK = (34, 38, 48)

# ---------------------------------------------------------------------------
# Type scale — strict. Six sizes and no others.
# ---------------------------------------------------------------------------
DISPLAY = 34                     # the question, once
TITLE = 22                       # screen titles
HEADING = 16                     # the clock
BODY = 14                        # prompts, chronicle lines
SMALL = 12                       # labels, log
MICRO = 11                       # bar readouts

# Bold is used in exactly two places: the opening question and the last line of
# the chronicle. Everywhere else it muddies the monospace.

LINE = 1.5                       # line height multiplier for stacked text


def line_step(size: int) -> int:
    """Vertical rhythm for a given type size."""
    return int(round(size * LINE))


# ---------------------------------------------------------------------------
# Spacing — an 8pt grid, so nothing is placed by eye
# ---------------------------------------------------------------------------
SPACE_1 = 8
SPACE_2 = 16
SPACE_3 = 24
SPACE_4 = 32
SPACE_6 = 48
SPACE_8 = 64

MARGIN = SPACE_3


def with_alpha(colour: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    """An RGBA of `colour` at 0..1 opacity."""
    return (*colour, max(0, min(255, int(255 * alpha))))
