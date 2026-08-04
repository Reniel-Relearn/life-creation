"""The look, held to its own rules.

Contrast and type scale are the two things that rot silently: a colour gets
nudged one shade to look nicer on the author's monitor and quietly stops being
readable, or a screen invents a fourteenth font size. Both are cheap to assert,
so they are asserted.

The palette this replaced had a grey at 2.68:1 doing real work in the opening
menu and the event log. That is the failure this file exists to prevent.
"""

from __future__ import annotations

import pytest

from life_creation.presentation import theme

AA_NORMAL = 4.5


def _linear(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_linear(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# Every colour that carries meaning, and must therefore be readable.
MEANINGFUL = {
    "INK": theme.INK,
    "MUTED": theme.MUTED,
    "SUBTLE": theme.SUBTLE,
    "EMBER": theme.EMBER,
    "SOUL": theme.SOUL,
    "ALARM": theme.ALARM,
}

TYPE_SCALE = (theme.MICRO, theme.SMALL, theme.BODY, theme.HEADING,
              theme.TITLE, theme.DISPLAY)


@pytest.mark.parametrize("name", sorted(MEANINGFUL))
def test_meaningful_text_clears_wcag_aa_on_the_backdrop(name):
    ratio = contrast(MEANINGFUL[name], theme.BACKDROP)
    assert ratio >= AA_NORMAL, f"{name} is {ratio:.2f}:1, needs {AA_NORMAL}:1"


@pytest.mark.parametrize("name", sorted(MEANINGFUL))
def test_meaningful_text_stays_readable_over_the_scrim(name):
    """The HUD sits on a wash, not on the raw backdrop."""
    ratio = contrast(MEANINGFUL[name], theme.SCRIM)
    assert ratio >= AA_NORMAL, f"{name} on scrim is {ratio:.2f}:1"


def test_unknown_land_is_distinct_from_the_backdrop():
    """The world must have a visible edge, or it reads as an unfinished window."""
    assert theme.UNKNOWN_LAND != theme.BACKDROP
    assert luminance(theme.UNKNOWN_LAND) > luminance(theme.BACKDROP)


def test_decor_is_declared_decorative_and_never_used_for_prose():
    """It is below the contrast line on purpose - so nothing may read from it."""
    assert contrast(theme.DECOR, theme.BACKDROP) < AA_NORMAL

    from pathlib import Path

    presentation = Path(theme.__file__).parent
    for path in presentation.rglob("*.py"):
        if path.name == "theme.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "theme.DECOR" not in text, (
            f"{path.name} uses DECOR, which is below the contrast line")


def test_bar_colours_are_distinguishable_from_their_track():
    for name, colour in (("good", theme.BAR_GOOD), ("warn", theme.BAR_WARN),
                         ("bad", theme.BAR_BAD)):
        ratio = contrast(colour, theme.BAR_TRACK)
        assert ratio >= 2.0, f"{name} bar is {ratio:.2f}:1 against its track"


def test_the_type_scale_is_strictly_ordered_with_no_duplicates():
    assert list(TYPE_SCALE) == sorted(TYPE_SCALE)
    assert len(set(TYPE_SCALE)) == len(TYPE_SCALE)


def test_body_text_is_never_smaller_than_eleven_points():
    assert min(TYPE_SCALE) >= 11


def test_no_screen_invents_a_size_outside_the_scale():
    """Six sizes, no in-between. Mono loses its character when rescaled at whim."""
    import ast
    from pathlib import Path

    allowed = set(TYPE_SCALE)
    presentation = Path(theme.__file__).parent
    offenders: list[str] = []

    for path in presentation.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Text"):
                continue
            # arcade.Text(text, x, y, colour, font_size, ...)
            if len(node.args) >= 5 and isinstance(node.args[4], ast.Constant):
                size = node.args[4].value
                if isinstance(size, int) and size not in allowed:
                    offenders.append(f"{path.name}:{node.lineno} size {size}")

    assert not offenders, "font sizes outside the scale: " + ", ".join(offenders)


def test_spacing_sits_on_the_eight_point_grid():
    for value in (theme.SPACE_1, theme.SPACE_2, theme.SPACE_3, theme.SPACE_4,
                  theme.SPACE_6, theme.SPACE_8, theme.MARGIN):
        assert value % 8 == 0, f"{value} is off the 8pt grid"


def test_with_alpha_clamps_rather_than_overflowing():
    assert theme.with_alpha(theme.INK, 0.0)[3] == 0
    assert theme.with_alpha(theme.INK, 1.0)[3] == 255
    assert theme.with_alpha(theme.INK, 2.5)[3] == 255
    assert theme.with_alpha(theme.INK, -1.0)[3] == 0
